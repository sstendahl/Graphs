# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing columns files."""
import re
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs import item, misc, utilities
from graphs.misc import ParseError


_PH = "dVldZaXqENhuPLPw"


def import_from_columns(params, style) -> misc.ItemList:
    """Import data from columns file."""
    file = params.get_file()
    item_ = item.DataItem.new(style, name=Graphs.tools_get_filename(file))
    column_x = params.get_int("column-x")
    column_y = params.get_int("column-y")
    separator = misc.SEPARATORS[params.get_string("separator")]
    skip_rows = params.get_int("skip-rows")
    delimiter = misc.DELIMITERS[params.get_string("delimiter")]
    if delimiter == "custom":
        delimiter = params.get_string("custom-delimiter")
    stream = Gio.DataInputStream.new(file.read(None))
    start_values = False
    for index, line in enumerate(stream, -skip_rows):
        if index < 0:
            continue
        values = re.split(delimiter, line)
        if separator == ",":
            values = [
                string.replace(",", _PH).replace(".", ", ").replace(_PH, ".")
                for string in values
            ]
        try:
            if len(values) == 1:
                float_value = utilities.string_to_float(values[0])
                if float_value is not None:
                    item_.ydata.append(float_value)
                    item_.xdata.append(index)
                    start_values = True
            else:
                try:
                    x_value = utilities.string_to_float(values[column_x])
                    y_value = utilities.string_to_float(values[column_y])
                    if x_value is None or y_value is None:
                        raise ValueError
                    item_.xdata.append(x_value)
                    item_.ydata.append(y_value)
                    start_values = True
                except IndexError as error:
                    raise ParseError(
                        _("Import failed, column index out of range"),
                    ) from error
        # If not all values in the line are floats, start looking for
        # headers instead
        except ValueError:
            # Don't try to add headers when started adding values
            if not start_values:
                try:
                    headers = re.split(delimiter, line)
                    if len(values) == 1:
                        item_.set_ylabel(headers[column_x])
                    else:
                        item_.set_xlabel(headers[column_x])
                        item_.set_ylabel(headers[column_y])
                # If no label could be found at the index, skip.
                except IndexError:
                    pass
    stream.close()
    if not item_.xdata:
        raise ParseError(_("Unable to import from file"))
    return [item_]
