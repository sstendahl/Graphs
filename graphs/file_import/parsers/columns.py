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
        parser.connect(
            "parse-float-request",
            ColumnsParser._on_parse_float_request,
        )

        try:
            parser.parse()
            yindex = settings.get_int("column-y")
            ylabel = parser.get_header(yindex)

            if settings.get_boolean("single-column"):
                xlabel = ""
                ydata = parser.get_column(yindex)
                equation = settings.get_string("single-equation")
                xdata = numexpr.evaluate(
                    utilities.preprocess(equation) + " + n*0",
                    local_dict={"n": numpy.arange(len(ydata))},
                )
                xdata = numpy.ndarray.tolist(xdata)
            else:
                xindex = settings.get_int("column-x")
                xdata, ydata = parser.get_column_pair(xindex, yindex)
                xlabel = parser.get_header(xindex)
        except GLib.Error as e:
            raise ParseError(e.message) from e

        return [
            item.DataItem.new(
                style,
                xdata,
                ydata,
                xlabel=xlabel,
                ylabel=ylabel,
                name=settings.get_filename(),
            ),
        ]

    @staticmethod
    def _on_parse_float_request(parser, string: str) -> bool:
        """Handle parse float request from Vala."""
        value = utilities.string_to_float(string)
        if value is None:
            return False
        parser.set_parse_float_helper(value)
        return True

    @staticmethod
    def init_settings_widgets(settings, box) -> None:
        """Append columns specific settings."""
        box.append(Graphs.ColumnsGroup.new(settings))
