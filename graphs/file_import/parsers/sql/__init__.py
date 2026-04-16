# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing sql files."""
from gettext import pgettext as C_

from gi.repository import GLib, Graphs, Gtk

from graphs.file_import.parsers import Parser
from graphs.misc import ParseError


class SqlParser(Parser):
    """SQL database parser."""

    __gtype_name__ = "GraphsSqlParser"

    def __init__(self):
        super().__init__(
            "sql",
            C_("import-mode", "Database"),
            C_("file-filter", "SQLite Database"),
            ["db", "sqlite", "sqlite3"],
        )

    @staticmethod
    def parse(
        items: Graphs.ItemList,
        settings: Graphs.ImportSettings,
        data: Graphs.Data,
    ) -> None:
        """Import data from sqlite database file."""
        db_reader = settings.get_item("db-reader")
        msg = db_reader.parse(items, settings, data)
        if msg != "":
            raise ParseError(msg)

    @staticmethod
    def init_settings(settings: Graphs.ImportSettings) -> bool:
        """Init settings with default table and column selection."""
        try:
            db_reader = Graphs.DatabaseReader.new(settings)
            db_reader.set_default_selection()
            settings.set_item("db-reader", db_reader)
            return True
        except GLib.GError:
            return False

    @staticmethod
    def init_settings_widgets(
        settings: Graphs.ImportSettings,
        box: Gtk.Box,
    ) -> None:
        """Append SQL-specific settings widgets."""
        if not settings.get_item("db-reader"):
            return
        box.append(Graphs.SqlGroup.new(settings))
