# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing spreadsheet files (ODS/XLSX)."""
import xml.etree.ElementTree
import zipfile
from gettext import gettext as _
from gettext import pgettext as C_
from itertools import zip_longest
from typing import List, Tuple

from gi.repository import GLib, Graphs, Gtk

from graphs import item, utilities
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

    def get_sheet_names(self, path: str) -> List[str]:
        """Get sheet names from ODS file."""
        with zipfile.ZipFile(path) as zip_file, \
             zip_file.open("content.xml") as content_file:
            root = xml.etree.ElementTree.parse(content_file).getroot()
            namespaces = {"table": ODS_TABLE_NAMESPACE}
            sheets = root.findall(".//table:table", namespaces)
            attribute_name = f"{{{namespaces['table']}}}name"
            return [sheet.get(attribute_name) for sheet in sheets]

    def parse_file(self, path: str, sheet_index: int) -> List[List[str]]:
        """Parse ODS file and return 2D array of column values."""
        with zipfile.ZipFile(path) as zip_file, \
             zip_file.open("content.xml") as content_file:
            root = xml.etree.ElementTree.parse(content_file).getroot()
            namespaces = {"table": ODS_TABLE_NAMESPACE}
            repeat_key = f"{{{namespaces['table']}}}number-columns-repeated"
            sheets = root.findall(".//table:table", namespaces)

            rows = []
            table_rows = \
                sheets[sheet_index].findall("table:table-row", namespaces)
            for table_row in table_rows:
                row_data = []
                cells = table_row.findall("table:table-cell", namespaces)
                for table_cell in cells:
                    repeat_count = int(table_cell.get(repeat_key, 1))
                    cell_value = "".join(table_cell.itertext())

                    for _count in range(repeat_count):
                        row_data.append(cell_value)
                rows.append(row_data)

            return [list(col) for col in zip_longest(*rows, fillvalue="")]


class XlsxParser:
    """XLSX file parser."""

    def get_sheet_names(self, path: str) -> List[str]:
        """Get sheet names from XLSX file."""
        with zipfile.ZipFile(path) as zip_file, \
             zip_file.open("xl/workbook.xml") as workbook_file:
            root = xml.etree.ElementTree.parse(workbook_file).getroot()
            namespaces = {"main": XLSX_MAIN_NAMESPACE}
            sheets = root.findall(f".//{{{namespaces['main']}}}sheet")
            return [sheet.get("name") for sheet in sheets]

    def parse_file(self, path: str, sheet_index: int) -> List[List[str]]:
        """Parse XLSX file and return 2D array of cell values."""
        with zipfile.ZipFile(path) as zip_file:
            shared_strings = self._load_shared_strings(zip_file)
            return self._parse_worksheet(zip_file, sheet_index, shared_strings)

    def _load_shared_strings(self, zip_file: zipfile.ZipFile) -> List[str]:
        """Load shared strings from XLSX file."""
        with zip_file.open("xl/sharedStrings.xml") as strings_file:
            root = xml.etree.ElementTree.parse(strings_file).getroot()
            namespace = XLSX_MAIN_NAMESPACE
            text_elements = root.findall(f".//{{{namespace}}}t")
            return [element.text or "" for element in text_elements]

    def _parse_worksheet(
        self,
        zip_file: zipfile.ZipFile,
        sheet_index: int,
        shared_strings: List[str],
    ) -> List[List[str]]:
        """Parse worksheet and return columns."""
        sheet_file = f"xl/worksheets/sheet{sheet_index + 1}.xml"

        with zip_file.open(sheet_file) as worksheet_file:
            root = xml.etree.ElementTree.parse(worksheet_file).getroot()
            namespaces = {"main": XLSX_MAIN_NAMESPACE}

            rows = []
            row_elements = root.findall(".//main:row", namespaces)

            for row_element in row_elements:
                row_data = \
                    self._parse_row(row_element, namespaces, shared_strings)
                rows.append(row_data)

            return [list(col) for col in zip_longest(*rows, fillvalue="")]

    def _parse_row(
        self,
        row_element,
        namespaces: dict,
        shared_strings: List[str],
    ) -> List[str]:
        """Parse a single row element."""
        row_data = []
        cell_elements = row_element.findall("main:c", namespaces)

        for current_col, cell_element in enumerate(cell_elements):
            ref = cell_element.get("r")
            column = "".join(c for c in ref if not c.isdigit())
            target_col = Graphs.SpreadsheetUtils.label_to_index(column)

            # Fill empty columns, first column in data might not correspond to
            # column A. So need to adjust current_col index accordingly.
            while current_col < target_col:
                row_data.append("")
                current_col += 1

            cell_string = self._get_cell_value(
                cell_element,
                namespaces,
                shared_strings,
            )
            row_data.append(cell_string)
            current_col += 1

        return row_data

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

    __gtype_name__ = "GraphsSpreadsheetParser"

    def __init__(self):
        super().__init__(
            "spreadsheet",
            C_("import-mode", "Spreadsheet"),
            C_("file-filter", "Spreadsheet (.ods, .xlsx)"),
            ["ods", "xlsx"],
        )

    @staticmethod
    def init_settings(settings: Graphs.ImportSettings) -> bool:
        """Init settings with default spreadsheet sheet selection."""
        file_path = settings.get_file().get_path()

        if file_path.endswith(".ods"):
            parser = OdsParser()
        elif file_path.endswith(".xlsx"):
            parser = XlsxParser()
        else:
            return False

        try:
            sheet_names = parser.get_sheet_names(file_path)
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

        group = Graphs.SpreadsheetGroup.new(settings)
        box.append(group)

        spreadsheet_box = Graphs.SpreadsheetBox.new(settings)
        box.append(spreadsheet_box)

    @staticmethod
    def parse(
        settings: Graphs.ImportSettings,
        style: Tuple[RcParams, dict],
    ) -> list:
        """Import data from ODS or XLSX file."""
        file_path = settings.get_file().get_path()
        sheet_index = settings.get_int("sheet-index")

        if file_path.endswith(".ods"):
            file_parser = OdsParser()
        else:
            file_parser = XlsxParser()

        columns = file_parser.parse_file(file_path, sheet_index)
        if not columns:
            raise ParseError(_("No data found in the selected sheet."))

        items = []
        item_settings = Graphs.ColumnsItemSettings()

        for item_string in settings.get_string("items").split(";;"):
            item_settings.load_from_item_string(item_string)

            x_index = item_settings.column_x
            y_index = item_settings.column_y

            if x_index >= len(columns) or y_index >= len(columns):
                raise ParseError(_("Column index out of range"))

            parser = Graphs.SpreadsheetDataParser.new(
                settings,
                columns[x_index],
                columns[y_index],
            )

            try:
                xdata, ydata = parser.get_data()
            except GLib.Error as e:
                raise ParseError(e.message) from e

            if len(xdata) != len(ydata):
                raise ParseError(
                    _("Selected columns do not have the same length."))

            xlabel = parser.get_x_header()
            ylabel = parser.get_y_header()

            if item_settings.single_column:
                xlabel = ""
                equation = item_settings.equation
                xdata = numexpr.evaluate(
                    utilities.preprocess(equation) + " + n*0",
                    local_dict={"n": numpy.arange(len(ydata))},
                )
                xdata = numpy.ndarray.tolist(xdata)

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
