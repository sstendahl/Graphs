# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing spreadsheet files (ODS/XLSX)."""
from gettext import pgettext as C_

from gi.repository import GLib, Graphs, Gtk

from graphs.file_import.parsers import Parser


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
