# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing columns files."""
import re
from gettext import pgettext as C_

from gi.repository import GLib, Graphs

from graphs import item, utilities
from graphs.file_import.parsers import Parser
from graphs.misc import ParseError

import numexpr


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
        parser.connect(
            "evaluate-equation-request",
            ColumnsParser._on_evaluate_equation_request,
        )

        try:
            parser.parse()
            # TODO: single-column-support
            x_index = settings.get_int("column-x")
            y_index = settings.get_int("column-y")
            xdata, ydata = parser.get_column_pair(x_index, y_index)
            xlabel = parser.get_header(x_index)
            ylabel = parser.get_header(y_index)
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
    def _on_evaluate_equation_request(
        parser,
        equation: str,
        index: int,
    ) -> bool:
        """Handle equation evaluation request from Vala."""
        equation = utilities.preprocess(equation)
        # Use word boundaries to avoid replacing `n` in function names
        string_value = re.sub(r"\bn\b", f"{index}", equation)
        value = numexpr.evaluate(string_value)
        if value is None:
            return False

        parser.set_evaluate_equation_helper(value)
        return True

    @staticmethod
    def init_settings_widgets(settings, box) -> None:
        """Append columns specific settings."""
        box.append(Graphs.ColumnsGroup.new(settings))
