# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing xry files."""
from gettext import gettext as _
from gettext import pgettext as C_

from gi.repository import Graphs

from graphs import item, misc
from graphs.file_import.parsers import Parser


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

        item_count, text_item_count = parser.parse(settings.get_file())

        name = settings.get_filename()
        items = []

        for i in range(item_count):
            xdata, ydata = parser.get_data_pair(i)
            items.append(
                item.DataItem.new(
                    style,
                    xdata,
                    ydata,
                    name=f"{name} - {i + 1}" if item_count > 1 else name,
                    xlabel=_("β (°)"),
                    ylabel=_("R (1/s)"),
                ),
            )

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
