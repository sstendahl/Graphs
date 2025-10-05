# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing columns files."""
from gettext import gettext as _
from gettext import pgettext as C_

from gi.repository import GLib, Graphs

from graphs import item, misc, utilities
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
        parser = Graphs.ColumnsParser.new(settings)
        try:
            xvalues, yvalues = parser.parse()
        except GLib.Error as e:
            raise ParseError(e.message) from e

        single_column = settings.get_boolean("single-column")

        xlabel = ""
        ylabel = ""
        xdata = []
        ydata = []

        for index, (xval, yval) in enumerate(zip(xvalues, yvalues)):
            x = utilities.string_to_float(xval)
            y = utilities.string_to_float(yval)

            # If values are None, we're likely looking at headers
            if y is None or (x is None and not single_column):
                if not xdata:
                    xlabel = "" if single_column else xval
                    ylabel = yval
                    continue
                else:
                    msg = _("Can't import from file, bad value on line "
                            f"{index}")
                    raise ParseError(msg)
            if single_column:
                xdata.append(index + 1)
                ydata.append(y)
            else:
                xdata.append(x)
                ydata.append(y)

        if not xdata:
            msg = _("Unable to import from file: no valid data found")
            raise ParseError(msg)

        return [item.DataItem.new(
            style, xdata, ydata,
            xlabel=xlabel, ylabel=ylabel,
            name=settings.get_filename(),
        )]

    @staticmethod
    def init_settings_widgets(settings, box) -> None:
        """Append columns specific settings."""
        box.append(Graphs.ColumnsGroup.new(settings))
