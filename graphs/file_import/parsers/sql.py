# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing sql files."""
from gettext import gettext as _
from gettext import pgettext as C_
from typing import Tuple

from gi.repository import Graphs, Gtk

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
    def parse(settings: Graphs.ImportSettings,
              style: Tuple[RcParams, dict],
              ) -> misc.ItemList:
        """Import data from sqlite database file."""
        db_reader = Graphs.DatabaseReader.new(settings.get_file())
        table_name = settings.sql_selection.get_table_name()
        x_column = settings.sql_selection.get_x_column()
        y_column = settings.sql_selection.get_y_column()

        xdata = db_reader.get_column_data(table_name, x_column)
        ydata = db_reader.get_column_data(table_name, y_column)

        item_name = settings.get_file().get_basename()
        item_ = item.DataItem.new(style, name=item_name)

        for x_val, y_val in zip(xdata, ydata):
            item_.xdata.append(x_val)
            item_.ydata.append(y_val)

        if len(item_.xdata) == 0 or len(item_.ydata) == 0:
            raise ParseError(_("Unable to import data from database, make sure"
                               " the entries contain real-valued numbers"))

        item_.set_xlabel(settings.sql_selection.get_x_column())
        item_.set_ylabel(settings.sql_selection.get_y_column())

        return [item_]

    @staticmethod
    def init_settings(settings: Graphs.ImportSettings) -> None:
        """Init settings with default table and column selection."""
        db_reader = Graphs.DatabaseReader.new(settings.get_file())
        default_selection = db_reader.get_default_selection()
        settings.sql_selection = default_selection

    @staticmethod
    def init_settings_widgets(settings: Graphs.ImportSettings,
                              box: Gtk.Box,
                              ) -> None:
        """Append SQL-specific settings widgets."""
        db_reader = Graphs.DatabaseReader.new(settings.get_file())
        sql_group = Graphs.SqlGroup.new(db_reader, settings.sql_selection)
        box.append(sql_group)
