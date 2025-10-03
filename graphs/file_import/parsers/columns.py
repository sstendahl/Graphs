# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing columns files."""
from gettext import pgettext as C_

from gi.repository import GLib, Graphs

from graphs import item, misc
from graphs.file_import.parsers import Parser
from graphs.misc import ParseError


class ColumnsParser(Parser):
    """Columns parser."""

    def __init__(self):
        super().__init__(
            "columns",
            C_("import-mode", "Columns"),
            None,
            None,
        )

    @staticmethod
    def parse(settings, style) -> misc.ItemList:
        """Import data from columns file."""
        try:
            parser = Graphs.ColumnsParser.new(settings)
            xdata, ydata, xlabel, ylabel = parser.parse()
        except GLib.Error as e:
            raise ParseError(e.message) from e
        item_ = item.DataItem.new(style, xdata, ydata, xlabel=xlabel,
                                  ylabel=ylabel, name=settings.get_filename())
        return [item_]

    @staticmethod
    def init_settings_widgets(settings, box) -> None:
        """Append columns specific settings."""
        box.append(Graphs.ColumnsGroup.new(settings))
