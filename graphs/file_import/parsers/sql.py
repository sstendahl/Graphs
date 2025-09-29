# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing sql files."""
from gettext import gettext as _
from gettext import pgettext as C_
from pathlib import Path
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
        db_reader = Graphs.DatabaseReader.new(settings)
        table_name = settings.get_string("table_name")
        if db_reader.get_numeric_columns(table_name):
            x_column = settings.get_string("x_column")
            y_column = settings.get_string("y_column")
        else:
            msg = _('Could not import data from table "{table_name}", no'
                    " numeric columns were found.")
            msg = msg.format(table_name=table_name)
            raise ParseError(msg)

        xdata = db_reader.get_column_data(table_name, x_column)
        ydata = db_reader.get_column_data(table_name, y_column)
        filename = Path(settings.get_file().get_basename()).stem
        item_name = f"{filename} - {table_name}"
        item_ = item.DataItem.new(style, name=item_name)

        for x_val, y_val in zip(xdata, ydata):
            item_.xdata.append(x_val)
            item_.ydata.append(y_val)

        if len(item_.xdata) == 0:
            raise ParseError(_("No data found in table column"))

        return [item_]

    @staticmethod
    def init_settings(settings: Graphs.ImportSettings) -> None:
        """Init settings with default table and column selection."""
        db_reader = Graphs.DatabaseReader.new(settings)
        db_reader.set_default_selection()

    @staticmethod
    def init_settings_widgets(settings: Graphs.ImportSettings,
                              box: Gtk.Box,
                              ) -> None:
        """Append SQL-specific settings widgets."""
        db_reader = Graphs.DatabaseReader.new(settings)
        sql_group = Graphs.SqlGroup.new(db_reader)
        box.append(sql_group)
