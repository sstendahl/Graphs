# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing xry files."""
from gettext import gettext as _
from gettext import pgettext as C_

from gi.repository import Graphs

from graphs import item
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
    def parse(
        items: Graphs.ItemList,
        settings: Graphs.ImportSettings,
        data: Graphs.Data,
    ) -> None:
        """Import data from .xry files used by Leybold X-ray apparatus."""
        style = data.get_selected_style_params()
        parser = Graphs.XryParser.new()

        item_count = parser.parse(data, settings.get_file(), items)
        name = settings.get_filename()

        for i in range(item_count):
            xdata, ydata = parser.get_data_pair(i)
            items.add(
                item.DataItem.new(
                    style,
                    xdata,
                    ydata,
                    name=f"{name} - {i + 1}" if item_count > 1 else name,
                    xlabel=_("β (°)"),
                    ylabel=_("R (1/s)"),
                ),
            )
