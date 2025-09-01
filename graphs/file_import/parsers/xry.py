# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing xry files."""
from gettext import gettext as _
from gettext import pgettext as C_

from gi.repository import Graphs

from graphs import file_io, item, misc
from graphs.file_import.parsers import Parser
from graphs.misc import ParseError


class XryParser(Parser):
    """Xry parser."""

    __gtype_name__ = "GraphsXryParser"

    def __init__(self):
        super().__init__(
            "xry",
            C_("import-mode", "xry"),
            [".xry"],
        )

    @staticmethod
    def parse(settings, style) -> misc.ItemList:
        """Import data from .xry files used by Leybold X-ray apparatus."""
        with file_io.open(
            settings.get_file(),
            "rt",
            encoding="ISO-8859-1",
        ) as file_like:

            def skip(lines: int):
                for _count in range(lines):
                    next(file_like)

            if file_like.readline().strip() != "XR01":
                raise ParseError(_("Invalid .xry format"))
            skip(3)
            b_params = file_like.readline().strip().split()
            x_step = float(b_params[3])
            x_value = float(b_params[0])

            skip(12)
            info = file_like.readline().strip().split()
            item_count = int(info[0])

            name = Graphs.tools_get_filename(settings.get_file())
            items = [
                item.DataItem.new(
                    style,
                    name=f"{name} - {i + 1}" if item_count > 1 else name,
                    xlabel=_("β (°)"),
                    ylabel=_("R (1/s)"),
                ) for i in range(item_count)
            ]
            for _count in range(int(info[1])):
                values = file_like.readline().strip().split()
                for value, item_ in zip(values, items):
                    if value != "NaN":
                        item_.xdata.append(x_value)
                        item_.ydata.append(float(value))
                x_value += x_step
            skip(9 + item_count)
            for _count in range(int(file_like.readline().strip())):
                values = file_like.readline().strip().split()
                text = " ".join(values[7:])
                items.append(
                    item.TextItem.new(
                        style,
                        float(values[5]),
                        float(values[6]),
                        text,
                        name=text,
                    ),
                )
            return items
