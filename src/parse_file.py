# SPDX-License-Identifier: GPL-3.0-or-later
import re
from gettext import gettext as _

from graphs import file_io, item, migrate, misc, utilities
from graphs.misc import ParseError

import numpy


def import_from_project(_self, file):
    try:
        project = file_io.parse_json(file)
    except UnicodeDecodeError:
        project = migrate.migrate_project(file)
    return list(map(item.new_from_dict, project["data"]))


def import_from_xrdml(self, file):
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
    style = self.get_figure_style_manager().get_selected_style_params()
    return [item.DataItem.new(
        style, xdata, ydata, name=utilities.get_filename(file),
        xlabel=f"{scan_axis} ({unit})", ylabel=_("Intensity (cps)"),
    )]


def import_from_xry(self, file):
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
        style = self.get_figure_style_manager().get_selected_style_params()
        items = [
            item.DataItem.new(
                style, name=f"{name} - {i + 1}" if item_count > 1 else name,
                xlabel=_("β (°)"), ylabel=_("R (1/s)"),
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
            items.append(item.TextItem.new(
                style, float(values[5]), float(values[6]), text, name=text,
            ))
        return items


def _swap(string):
    string = string.replace(",", "third")
    string = string.replace(".", ", ")
    return string.replace("third", ".")


def import_from_columns(self, file):
    style = self.get_figure_style_manager().get_selected_style_params()
    item_ = item.DataItem.new(style, name=utilities.get_filename(file))
    columns_params = self.get_settings().get_child(
        "import-params").get_child("columns")
    column_x = columns_params.get_int("column-x")
    column_y = columns_params.get_int("column-y")
    separator = columns_params.get_string("separator").replace(" ", "")
    skip_rows = columns_params.get_int("skip-rows")
    delimiter = misc.DELIMITERS[columns_params.get_string("delimiter")]
    if delimiter == "custom":
        delimiter = columns_params.get_string("custom-delimiter")
    with file_io.open_wrapped(file, "rt") as wrapper:
        for index, line in enumerate(wrapper, -skip_rows):
            if index < 0:
                continue
            values = re.split(delimiter, line.strip())
            if separator == ",":
                values = list(map(_swap, values))
            try:
                if len(values) == 1:
                    float_value = utilities.string_to_float(values[0])
                    if float_value is not None:
                        item_.ydata.append(float_value)
                        item_.xdata.append(index)
                else:
                    try:
                        item_.xdata.append(utilities.string_to_float(
                            values[column_x]))
                        item_.ydata.append(utilities.string_to_float(
                            values[column_y]))
                    except IndexError as error:
                        raise ParseError(
                            _("Import failed, column index out of range"),
                        ) from error
            # If not all values in the line are floats, start looking for
            # headers instead
            except ValueError:
                # By default it will check for headers using at least
                # two whitespaces as delimiter (often tabs), but if
                # that doesn"t work it will try the same delimiter as
                # used for the data import itself The reasoning is that
                # some people use tabs for the headers, but e.g. commas
                # for the data
                try:
                    headers = re.split("\\s{2,}", line)
                    if len(values) == 1:
                        item_.ylabel = headers[column_x]
                    else:
                        item_.xlabel = headers[column_x]
                        item_.ylabel = headers[column_y]
                except IndexError:
                    try:
                        headers = re.split(delimiter, line)
                        if len(values) == 1:
                            item_.ylabel = headers[column_x]
                        else:
                            item_.xlabel = headers[column_x]
                            item_.ylabel = headers[column_y]
                    # If neither heuristic works, we just skip headers
                    except IndexError:
                        pass
    if not item_.xdata:
        raise ParseError(_("Unable to import from file"))
    return [item_]
