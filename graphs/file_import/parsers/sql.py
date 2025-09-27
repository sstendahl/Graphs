# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for "parsing" project files."""
import logging
from gettext import gettext as _
from gettext import pgettext as C_

from gi.repository import GLib, Graphs

from graphs import item, misc
from graphs.file_import.parsers import Parser
from graphs.misc import ParseError


class SqlParser(Parser):
    """Project parser."""

    __gtype_name__ = "GraphsSqlParser"

    def __init__(self):
        super().__init__(
            "project",
            C_("import-mode", "Database"),
            C_("file-filter", "SQLite Database"),
            ["db"],
        )

    def parse(self, _settings, style) -> misc.ItemList:
        """Import data from sqlite database file."""
        data = self.sql_group.get_selected_data()
        item_name = data.name
        selected_xdata = data.xdata
        selected_ydata = data.ydata
        xlabel = data.x_column_name
        ylabel = data.y_column_name
        item_ = item.DataItem.new(style, name=item_name)

        for xdata, ydata in zip(selected_xdata, selected_ydata):
            item_.xdata.append(xdata)
            item_.ydata.append(ydata)

        if not item_.xdata:
            raise ParseError(_("Unable to import data from database, make sure"
                               " the entries contain real-valued numbers"))
        item_.set_xlabel(xlabel)
        item_.set_ylabel(ylabel)
        return [item_]

    def init_settings_widgets(self, settings, box) -> None:
        """Append SQL-specific settings widgets."""
        file = settings.get_file()
        try:
            self.sql_group = Graphs.SqlGroup.new(file)
        except GLib.Error as error:
            logging.error(error)
            return
        box.append(self.sql_group)
