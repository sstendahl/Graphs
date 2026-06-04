# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing spreadsheet files (ODS/XLSX)."""
import xml.etree.ElementTree
import zipfile
from gettext import pgettext as C_

from gi.repository import GLib, Gio, Graphs, Gtk

from graphs import file_io
from graphs.file_import.parsers import Parser

# XML Namespaces
XLSX_MAIN_NAMESPACE = \
    "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


class XlsxParser:
    """XLSX file parser."""

    def parse_file(
        self,
        file: Gio.File,
        columns: set[int],
        sheet_index: int,
    ) -> list[tuple[str, list[float]]]:
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

    def _load_shared_strings(self, zip_file: zipfile.ZipFile) -> list[str]:
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
        shared_strings: list[str],
    ) -> list[list[str]]:
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
        shared_strings: list[str],
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
        shared_strings: list[str],
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
        try:
            parser = Graphs.SpreadsheetParser.new(settings.get_file())
            settings.set_item("parser", parser)
            return True
        except GLib.GError:
            return False

    @staticmethod
    def init_settings_widgets(
        settings: Graphs.ImportSettings,
        box: Gtk.Box,
    ) -> None:
        """Append Spreadsheet-specific settings widgets."""
        if not settings.get_item("parser"):
            return
        box.append(Graphs.SpreadsheetGroup.new(settings))
        box.append(Graphs.SpreadsheetBox.new(settings))

    @staticmethod
    def parse(
        items: Graphs.ItemList,
        settings: Graphs.ImportSettings,
        data: Graphs.Data,
    ) -> None:
        """Import data from ODS or XLSX file."""
        settings.get_item("parser").parse(settings, data, items)
