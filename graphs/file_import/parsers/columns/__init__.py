# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing columns files."""
from gettext import pgettext as C_

from gi.repository import GLib, Graphs

from graphs import item, utilities
from graphs.file_import.parsers import Parser
from graphs.misc import ParseError

import numexpr

import numpy


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
    def parse(settings, style) -> list:
        """Import data from columns file."""
        parser = Graphs.ColumnsParser.new(settings)

        try:
            parser.parse()
        except GLib.Error as e:
            raise ParseError(e.message) from e

        items = []
        for item_string in settings.get_string("items").split(";;"):
            item_settings = Graphs.ColumnsItemSettings()
            item_settings.load_from_item_string(item_string)

            yindex = item_settings.column_y
            ylabel = parser.get_header(yindex)
            ydata = parser.get_column(yindex)

            if item_settings.single_column:
                xlabel = ""
                equation = item_settings.equation
                xdata = numexpr.evaluate(
                    utilities.preprocess(equation) + " + n*0",
                    local_dict={"n": numpy.arange(len(ydata))},
                )
                xdata = numpy.ndarray.tolist(xdata)
            else:
                xindex = item_settings.column_x
                xdata = parser.get_column(xindex)
                xlabel = parser.get_header(xindex)

            items.append(
                item.DataItem.new(
                    style,
                    xdata,
                    ydata,
                    xlabel=xlabel,
                    ylabel=ylabel,
                    name=settings.get_filename(),
                ),
            )

        return items

    @staticmethod
    def init_settings_widgets(settings, box) -> None:
        """Append columns specific settings."""
        box.append(Graphs.ColumnsBox.new(settings))
