import re
from gettext import gettext as _

from graphs import file_io, item, utilities
from graphs.misc import ParseError

import numpy


def import_from_project(_self, file):
    return [item.new_from_dict(dictionary)
            for dictionary in file_io.parse_json(file)["data"]]


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
        scan_axis = _("2Theta")
    if scan_axis.startswith("Omega"):
        scan_axis = _("Omega")

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
    return [item.Item.new(
        self, xdata, ydata, name=utilities.get_filename(file),
        xlabel=f"{scan_axis} ({unit})", ylabel=_("Intensity (cps)"))]


def import_from_xry(self, file):
    """Import data from .xry files used by Leybold X-ray apparatus."""
    lines = file_io.read_file(file, encoding="ISO-8859-1").splitlines()
    if lines[0].strip() != "XR01":
        raise ParseError(_("Invalid .xry format"))

    b_params = lines[4].strip().split()
    b_min = float(b_params[0])
    b_step = float(b_params[3])

    info = lines[17].strip().split()
    value_count = int(info[1])
    item_count = int(info[0])

    items = []
    for i in range(item_count):
        name = utilities.get_filename(file)
        if item_count > 1:
            name += f" - {i + 1}"
        items.append(item.Item.new(
            self, name=name, xlabel=_("β (°)"), ylabel=_("R (1/s)"),
        ))
    for i in range(value_count):
        values = lines[18 + i].strip().split()
        for j in range(item_count):
            value = values[j]
            if value != "NaN":
                items[j].xdata.append(b_step * i + b_min)
                items[j].ydata.append(float(value))
    for row in lines[28 + value_count + item_count:]:
        values = row.strip().split()
        text = " ".join(values[7:])
        items.append(item.TextItem.new(
            self, float(values[5]), float(values[6]), text, name=text))
    return items


def import_from_columns(self, file):
    item_ = item.Item.new(self, name=utilities.get_filename(file))
    columns_params = self.get_settings().get_child(
        "import-params").get_child("columns")
    column_x = columns_params.get_int("column-x")
    column_y = columns_params.get_int("column-y")
    delimiter = columns_params.get_string("delimiter")
    separator = columns_params.get_string("separator").replace(" ", "")
    skip_rows = columns_params.get_int("skip-rows")
    for i, line in enumerate(file_io.read_file(file).splitlines()):
        if i >= skip_rows:
            data_line = re.split(delimiter, line.strip())
            if separator == ",":
                for index, value in enumerate(data_line):
                    data_line[index] = utilities.swap(value)
            try:
                if len(data_line) == 1:
                    float_value = utilities.string_to_float(data_line[0])
                    if float_value is not None:
                        item_.ydata.append(float_value)
                        item_.xdata.append(i)
                else:
                    try:
                        item_.xdata.append(utilities.string_to_float(
                            data_line[column_x]))
                        item_.ydata.append(utilities.string_to_float(
                            data_line[column_y]))
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
                    if len(data_line) == 1:
                        item_.ylabel = headers[column_x]
                    else:
                        item_.xlabel = headers[column_x]
                        item_.ylabel = headers[column_y]
                except IndexError:
                    try:
                        headers = re.split(delimiter, line)
                        if len(data_line) == 1:
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
