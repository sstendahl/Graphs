# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing columns files."""
from gettext import pgettext as C_

from gi.repository import GLib, Graphs

from graphs import item
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
        variant = settings.get_value("items")
        for i in range(variant.n_children()):
            item_settings = Graphs.ColumnsItemSettings()
            item_settings.load_from_variant(variant.get_child_value(i))

            ylabel = parser.get_header(item_settings.column_y)
            ydata = parser.get_column(item_settings.column_y)

            yerr = parser.get_column(item_settings.yerr_index) \
                if item_settings.use_yerr else None
            xerr = parser.get_column(item_settings.xerr_index) \
                if item_settings.use_xerr else None
            if item_settings.single_column:
                xlabel = ""
                xdata = numexpr.evaluate(
                    Graphs.preprocess_equation(item_settings.equation),
                    local_dict={"n": numpy.arange(len(ydata))},
                )
                if xdata.ndim == 0:
                    xdata = numpy.full(len(ydata), xdata)
                xdata = numpy.ndarray.tolist(xdata)
            else:
                xdata = parser.get_column(item_settings.column_x)
                xlabel = parser.get_header(item_settings.column_x)

            items.append(
                item.DataItem.new(
                    style,
                    xdata,
                    ydata,
                    xerr,
                    yerr,
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
