# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing xry files."""
from copy import copy

from gettext import gettext as _
from gettext import pgettext as C_

from gi.repository import Graphs

from graphs import file_io, item, misc
from graphs.file_import.parsers import Parser
from graphs.misc import ParseError


class XryParser(Parser):
    """Xry parser."""

    __gtype_name__ = "GraphsPythonXryParser"

    def __init__(self):
        super().__init__(
            "xry",
            C_("import-mode", "xry"),
            C_("file-filter", "Leybold xry"),
            ["xry"],
        )

    @staticmethod
    def parse(settings, style) -> misc.ItemList:
        """Import data from .xry files used by Leybold X-ray apparatus."""
        parser = Graphs.XryParser.new()

        parser.parse(settings.get_file())
        xdata = parser.get_xdata()

        name = settings.get_filename()
        items = []

        item_count = parser.get_item_count()
        for i in range(item_count):
            ydata = parser.get_ydata (i)
            items.append(
                item.DataItem.new(
                    style,
                    copy(xdata[:len(ydata)]),
                    ydata,
                    name=f"{name} - {i + 1}" if item_count > 1 else name,
                    xlabel=_("β (°)"),
                    ylabel=_("R (1/s)"),
                )
            )

        text_item_count = parser.get_text_item_count()
        for i in range(text_item_count):
            text, x, y = parser.get_text_data(i)
            items.append(
                item.TextItem.new(
                    style,
                    x,
                    y,
                    text,
                    name=text,
                ),
            )

        return items
