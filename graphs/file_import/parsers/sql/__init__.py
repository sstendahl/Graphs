# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing sql files."""
from gettext import gettext as _
from gettext import pgettext as C_
from typing import Tuple

from gi.repository import GLib, Graphs, Gtk

from graphs import item, misc
from graphs.file_import.parsers import Parser
from graphs.misc import ParseError

from matplotlib import RcParams


class SqlParser(Parser):
    """SQL database parser."""

    __gtype_name__ = "GraphsSqlParser"

    def __init__(self):
        super().__init__(
            "sql",
            C_("import-mode", "Database"),
            C_("file-filter", "SQLite Database"),
            ["db"],
        )

    @staticmethod
    def parse(
        settings: Graphs.ImportSettings,
        style: Tuple[RcParams, dict],
    ) -> misc.ItemList:
        """Import data from sqlite database file."""
        db_reader = settings.get_item("db-reader")
        table_name = settings.get_string("table-name")
        if db_reader.get_numeric_columns(table_name):
            x_column = settings.get_string("x-column")
            y_column = settings.get_string("y-column")
        else:
            msg = _(
                'Could not import data from table "{table_name}", no'
                " numeric columns were found",
            )
            msg = msg.format(table_name=table_name)
            raise ParseError(msg)

        xdata = db_reader.get_column_data(table_name, x_column)
        ydata = db_reader.get_column_data(table_name, y_column)

        if len(xdata) == 0:
            raise ParseError(_("No data found in table column"))

        xerr = None
        yerr = None
        if settings.get_boolean("use-xerr"):
            xerr = db_reader.get_column_data(
                table_name, settings.get_string("xerr-column"),
            )
        if settings.get_boolean("use-yerr"):
            yerr = db_reader.get_column_data(
                table_name, settings.get_string("yerr-column"),
            )

        return [
            item.DataItem.new(
                style,
                xdata=xdata,
                ydata=ydata,
                xerr=xerr,
                yerr=yerr,
                xlabel=x_column,
                ylabel=y_column,
                name=f"{x_column} vs {y_column}",
            ),
        ]

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
