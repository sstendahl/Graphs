# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing files to usable data."""
import re
from gettext import gettext as _

from gi.repository import Gio

from graphs import file_io, item, migrate, misc, utilities
from graphs.misc import ParseError

import numpy


def import_from_project(_params, _style, file: Gio.File) -> misc.ItemList:
    """Import data from project file."""
    try:
        project = file_io.parse_json(file)
    except UnicodeDecodeError:
        project = migrate.migrate_project(file)
    return list(map(item.new_from_dict, project["data"]))


def import_from_xrdml(_params, style, file: Gio.File) -> misc.ItemList:
    """Import data from xrdml file."""
    content = file_io.parse_xml(file)
    intensities = content.getElementsByTagName("intensities")
    counting_time = content.getElementsByTagName("commonCountingTime")
    counting_time = float(counting_time[0].firstChild.data)
    ydata = intensities[0].firstChild.data.split()
    ydata = [int(value) / counting_time for value in ydata]

    scan_type = content.getElementsByTagName("scan")
    scan_axis = scan_type[0].attributes["scanAxis"].value
    if scan_axis.startswith("2Theta"):
        scan_axis = "2Theta"
    if scan_axis.startswith("Omega"):
        scan_axis = "Omega"

    data_points = content.getElementsByTagName("positions")
    for position in data_points:
        axis = position.attributes["axis"]
        if axis.value == scan_axis:
            unit = position.attributes["unit"].value
            start_pos = position.getElementsByTagName("startPosition")
            end_pos = position.getElementsByTagName("endPosition")
            start_pos = float(start_pos[0].firstChild.data)
            end_pos = float(end_pos[0].firstChild.data)
            xdata = numpy.linspace(start_pos, end_pos, len(ydata))
            xdata = numpy.ndarray.tolist(xdata)
    return [
        item.DataItem.new(
            style,
            xdata,
            ydata,
            name=utilities.get_filename(file),
            xlabel=f"{scan_axis} ({unit})",
            ylabel=_("Intensity (cps)"),
        ),
    ]


def import_from_xry(_params, style, file: Gio.File) -> misc.ItemList:
    """Import data from .xry files used by Leybold X-ray apparatus."""
    with file_io.open_wrapped(file, "rt", encoding="ISO-8859-1") as wrapper:

        def skip(lines: int):
            for _count in range(lines):
                next(wrapper)

        if wrapper.readline().strip() != "XR01":
            raise ParseError(_("Invalid .xry format"))
        skip(3)
        b_params = wrapper.readline().strip().split()
        x_step = float(b_params[3])
        x_value = float(b_params[0])

        skip(12)
        info = wrapper.readline().strip().split()
        item_count = int(info[0])

        name = utilities.get_filename(file)
        items = [
            item.DataItem.new(
                style,
                name=f"{name} - {i + 1}" if item_count > 1 else name,
                xlabel=_("β (°)"),
                ylabel=_("R (1/s)"),
            ) for i in range(item_count)
        ]
        for _count in range(int(info[1])):
            for value, item_ in zip(wrapper.readline().strip().split(), items):
                if value != "NaN":
                    item_.xdata.append(x_value)
                    item_.ydata.append(float(value))
            x_value += x_step
        skip(9 + item_count)
        for _count in range(int(wrapper.readline().strip())):
            values = wrapper.readline().strip().split()
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


_PH = "dVldZaXqENhuPLPw"


def import_from_columns(params, style, file: Gio.File) -> misc.ItemList:
    """Import data from columns file."""
    item_ = item.DataItem.new(style, name=utilities.get_filename(file))
    column_x = params.get_int("column-x")
    column_y = params.get_int("column-y")
    separator = params.get_string("separator").replace(" ", "")
    skip_rows = params.get_int("skip-rows")
    delimiter = misc.DELIMITERS[params.get_string("delimiter")]
    if delimiter == "custom":
        delimiter = params.get_string("custom-delimiter")
    stream = Gio.DataInputStream.new(file.read(None))
    start_values = False
    for index, line in \
            enumerate(file_io.iter_data_stream(stream), -skip_rows):
        if index < 0:
            continue
        values = re.split(delimiter, line)
        if separator == ",":
            values = (
                string.replace(",", _PH).replace(".", ", ").replace(_PH, ".")
                for string in values
            )
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
                    else:
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
