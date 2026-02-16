# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing spreadsheet files (ODS/XLSX)."""
import xml.etree.ElementTree
import zipfile
from gettext import gettext as _
from gettext import pgettext as C_
from typing import List, Tuple

from gi.repository import GLib, Gio, Graphs, Gtk

from graphs import file_io, item
from graphs.file_import.parsers import Parser
from graphs.misc import ParseError

from matplotlib import RcParams

import numexpr

import numpy

# XML Namespaces
ODS_TABLE_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
XLSX_MAIN_NAMESPACE = \
    "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


class OdsParser:
    """ODS file parser."""

    def get_sheet_names(self, file: Gio.File) -> List[str]:
        """Get sheet names from ODS file."""
        with file_io.open(file, "rb") as file_obj, \
             zipfile.ZipFile(file_obj) as zip_file, \
             zip_file.open("content.xml") as content_file:
            root = xml.etree.ElementTree.parse(content_file).getroot()
            namespaces = {"table": ODS_TABLE_NAMESPACE}
            sheets = root.findall(".//table:table", namespaces)
            attribute_name = f"{{{namespaces['table']}}}name"
            return [sheet.get(attribute_name) for sheet in sheets]

    def parse_file(
        self,
        file: Gio.File,
        columns: set[int],
        sheet_index: int,
    ) -> List[Tuple[str, List[float]]]:
        """Parse ODS file and return list of requested columns."""
        with file_io.open(file, "rb") as file_obj, \
             zipfile.ZipFile(file_obj) as zip_file, \
             zip_file.open("content.xml") as content_file:
            root = xml.etree.ElementTree.parse(content_file).getroot()
            namespaces = {"table": ODS_TABLE_NAMESPACE}
            repeat_key = f"{{{namespaces['table']}}}number-columns-repeated"
            sheets = root.findall(".//table:table", namespaces)

            max_col = max(columns)
            raw_columns = {col_index: [[], ""] for col_index in columns}

            table_rows = sheets[sheet_index].findall(
                "table:table-row",
                namespaces,
            )
            for table_row in table_rows:
                cells = table_row.findall("table:table-cell", namespaces)
                current_col = 0

                for table_cell in cells:
                    repeat_count = int(table_cell.get(repeat_key, 1))
                    cell_value = "".join(table_cell.itertext())
                    for _count in range(repeat_count):
                        if current_col > max_col:
                            break
                        if current_col in columns:
                            try:
                                val = Graphs.evaluate_string(cell_value)
                                raw_columns[current_col][0].append(val)
                            except GLib.Error:
                                if len(raw_columns[current_col][0]) == 0:
                                    raw_columns[current_col][1] = \
                                        cell_value.strip()
                                else:
                                    break
                        current_col += 1
            return raw_columns


class XlsxParser:
    """XLSX file parser."""

    def get_sheet_names(self, file: Gio.File) -> List[str]:
        """Get sheet names from XLSX file."""
        with file_io.open(file, "rb") as file_obj, \
             zipfile.ZipFile(file_obj) as zip_file, \
             zip_file.open("xl/workbook.xml") as workbook_file:
            root = xml.etree.ElementTree.parse(workbook_file).getroot()
            namespaces = {"main": XLSX_MAIN_NAMESPACE}
            sheets = root.findall(f".//{{{namespaces['main']}}}sheet")
            return [sheet.get("name") for sheet in sheets]

    def parse_file(
        self,
        file: Gio.File,
        columns: set[int],
        sheet_index: int,
    ) -> List[Tuple[str, List[float]]]:
        """Parse XLSX file and return 2D array of cell values."""
        with file_io.open(file, "rb") as file_obj, \
             zipfile.ZipFile(file_obj) as zip_file:
            shared_strings = self._load_shared_strings(zip_file)
            return self._parse_worksheet(
                zip_file,
                columns,
                sheet_index,
                shared_strings,
            )

    def _load_shared_strings(self, zip_file: zipfile.ZipFile) -> List[str]:
        """Load shared strings from XLSX file."""
        try:
            with zip_file.open("xl/sharedStrings.xml") as strings_file:
                root = xml.etree.ElementTree.parse(strings_file).getroot()
                namespace = XLSX_MAIN_NAMESPACE
                text_elements = root.findall(f".//{{{namespace}}}t")
                return [element.text or "" for element in text_elements]
        except KeyError:
            return []  # No shared strings in this file

    def _parse_worksheet(
        self,
        zip_file: zipfile.ZipFile,
        columns: set[int],
        sheet_index: int,
        shared_strings: List[str],
    ) -> List[List[str]]:
        """Parse worksheet and return requested columns."""
        sheet_file = f"xl/worksheets/sheet{sheet_index + 1}.xml"
        with zip_file.open(sheet_file) as worksheet_file:
            root = xml.etree.ElementTree.parse(worksheet_file).getroot()
            namespaces = {"main": XLSX_MAIN_NAMESPACE}
            raw_columns = {col_index: [[], ""] for col_index in columns}
            for row_element in root.findall(".//main:row", namespaces):
                row_data = self._parse_row(
                    row_element,
                    namespaces,
                    shared_strings,
                    columns,
                )
                for col_index in columns:
                    cell_value = row_data.get(col_index, "")
                    try:
                        val = Graphs.evaluate_string(cell_value)
                        raw_columns[col_index][0].append(val)
                    except GLib.Error:
                        if len(raw_columns[col_index][0]) == 0:
                            raw_columns[col_index][1] = cell_value.strip()
                        else:
                            break
        return raw_columns

    def _parse_row(
        self,
        row_element,
        namespaces: dict,
        shared_strings: List[str],
        columns: set,
    ) -> dict:
        """Parse a single row element, returning only requested columns."""
        cell_elements = row_element.findall("main:c", namespaces)
        cell_data = {}

        for cell_element in cell_elements:
            ref = cell_element.get("r")
            column = "".join(c for c in ref if not c.isdigit())
            column_index = Graphs.tools_alpha_to_int(column)

            if column_index in columns:
                cell_data[column_index] = self._get_cell_value(
                    cell_element,
                    namespaces,
                    shared_strings,
                )
        return cell_data

    def _get_cell_value(
        self,
        cell_element,
        namespaces: dict,
        shared_strings: List[str],
    ) -> str:
        """Extract cell value, handling shared strings."""
        value = cell_element.find("main:v", namespaces)
        cell_string = value.text if value is not None else ""
        cell_type = cell_element.get("t")

        if cell_type == "s":  # Type s is for shared strings
            string_index = int(cell_string)
            cell_string = shared_strings[string_index]

        return cell_string


class SpreadsheetParser(Parser):
    """Main spreadsheet parser that delegates to ODS/XLSX parsers."""

    def __init__(self):
        super().__init__(
            "spreadsheet",
            C_("import-mode", "Spreadsheet"),
            C_("file-filter", "Spreadsheet"),
            ["ods", "xlsx"],
        )

    @staticmethod
    def init_settings(settings: Graphs.ImportSettings) -> bool:
        """Init settings with default spreadsheet sheet selection."""
        file = settings.get_file()
        parser = \
            OdsParser() if file.get_path().endswith(".ods") else XlsxParser()
        try:
            sheet_names = parser.get_sheet_names(file)
            string_list = Gtk.StringList.new(sheet_names)
            settings.set_item("sheet-names", string_list)
            return True
        except zipfile.BadZipFile:
            return False

    @staticmethod
    def init_settings_widgets(
        settings: Graphs.ImportSettings,
        box: Gtk.Box,
    ) -> None:
        """Append Spreadsheet-specific settings widgets."""
        if not settings.get_item("sheet-names"):
            return
        box.append(Graphs.SpreadsheetGroup.new(settings))
        box.append(Graphs.SpreadsheetBox.new(settings))

    @staticmethod
    def parse(
        settings: Graphs.ImportSettings,
        style: Tuple[RcParams, dict],
    ) -> list:
        """Import data from ODS or XLSX file."""
        file = settings.get_file()
        sheet_index = settings.get_int("sheet-index")

        column_indices = set()
        item_settings_list = []
        for item_string in settings.get_string("items").split(";;"):
            item_settings = Graphs.ColumnsItemSettings()
            item_settings.load_from_item_string(item_string)
            item_settings_list.append(item_settings)

            column_indices.add(item_settings.column_y)
            if not item_settings.single_column:
                column_indices.add(item_settings.column_x)

        file_parser = \
            OdsParser() if file.get_path().endswith(".ods") else XlsxParser()
        parsed_columns = file_parser.parse_file(
            file,
            column_indices,
            sheet_index,
        )

        items = []
        for item_settings in item_settings_list:
            yindex = item_settings.column_y
            ydata, ylabel = parsed_columns[yindex]

            if len(ydata) == 0:
                raise ParseError(_("No numeric data found in column."))

            if item_settings.single_column:
                xlabel = ""
                equation = item_settings.equation
                xdata = numexpr.evaluate(
                    Graphs.preprocess_equation(equation) + " + n*0",
                    local_dict={
                        "n": numpy.arange(len(ydata)),
                    },
                ).tolist()
            else:
                xindex = item_settings.column_x
                xdata, xlabel = parsed_columns[xindex]
                if len(xdata) != len(ydata):
                    raise ParseError(_("Columns do not have the same length."))

            items.append(
                item.DataItem.new(
                    style,
                    xdata,
                    ydata,
                    xlabel=xlabel,
                    ylabel=ylabel,
                    name=settings.get_filename(),
                ),
            )

        return items
