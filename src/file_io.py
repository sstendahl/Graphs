# SPDX-License-Identifier: GPL-3.0-or-later
import json
import logging
import re
from gettext import gettext as _
from pathlib import Path
from xml.dom import minidom

from gi.repository import GLib

from graphs import item, utilities
from graphs.item import Item, TextItem
from graphs.misc import ParseError

from matplotlib import RcParams, cbook
from matplotlib.style.core import STYLE_BLACKLIST

import numpy


def save_item(file, item_):
    delimiter = "\t"
    fmt = delimiter.join(["%.12e"] * 2)
    stream = _get_write_stream(file)
    if item_.xlabel != "" and item_.ylabel != "":
        _write_string(stream, item_.xlabel + delimiter + item_.ylabel + "\n")
    for row in numpy.stack([item_.xdata, item_.ydata], axis=1):
        _write_string(stream, fmt % tuple(row) + "\n")
    stream.close()


def import_from_project(_self, import_settings):
    return [item.new_from_dict(dictionary)
            for dictionary in parse_json(import_settings.file)["data"]]


def import_from_xrdml(self, import_settings):
    content = parse_xml(import_settings.file)
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
    return [Item.new(
        self, xdata, ydata, name=import_settings.name,
        xlabel=f"{scan_axis} ({unit})", ylabel=_("Intensity (cps)"))]


def import_from_xry(self, import_settings):
    """Import data from .xry files used by Leybold X-ray apparatus."""
    lines = read_file(import_settings.file, encoding="ISO-8859-1").splitlines()
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
        if item_count > 1:
            name = f"{import_settings.name} - {i + 1}"
        else:
            name = import_settings.name
        items.append(
            Item.new(self, name=name, xlabel=_("β (°)"), ylabel=_("R (1/s)")))
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
        items.append(TextItem.new(
            self, float(values[5]), float(values[6]), text, name=text))
    return items


def import_from_columns(self, import_settings):
    item_ = Item.new(self, name=import_settings.name)
    columns_params = self.settings.get_child(
        "import-params").get_child("columns")
    column_x = columns_params.get_int("column-x")
    column_y = columns_params.get_int("column-y")
    delimiter = columns_params.get_string("delimiter")
    separator = columns_params.get_string("separator").replace(" ", "")
    skip_rows = columns_params.get_int("skip-rows")
    for i, line in enumerate(read_file(import_settings.file).splitlines()):
        if i >= skip_rows:
            data_line = re.split(delimiter, line.strip())
            if separator == ",":
                for index, value in enumerate(data_line):
                    data_line[index] = utilities.swap(value)
            try:
                if len(data_line) == 1:
                    item_.xdata.append(i)
                    item_.ydata.append(utilities.string_to_float(data_line[0]))
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
                    item_.xlabel = headers[column_x]
                    item_.ylabel = headers[column_x]
                except IndexError:
                    try:
                        headers = re.split(delimiter, line)
                        item_.xlabel = headers[column_x]
                        item_.ylabel = headers[column_x]
                    # If neither heuristic works, we just skip headers
                    except IndexError:
                        pass
    if not item_.xdata:
        raise ParseError(_("Unable to import from file"))
    return [item_]


def parse_style(file):
    """
    Parse a style to RcParams.

    This is an improved version of matplotlibs '_rc_params_in_file()' function.
    It is also modified to work with GFile instead of the python builtin
    functions.
    """
    style = RcParams()
    filename = utilities.get_filename(file)
    try:
        for line_number, line in enumerate(read_file(file).splitlines(), 1):
            stripped_line = cbook._strip_comment(line)
            if not stripped_line:
                continue
            try:
                key, value = stripped_line.split(":", 1)
            except ValueError:
                logging.warning(
                    _("Missing colon in file {}, line {}").format(
                        filename, line_number))
                continue
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]  # strip double quotes
            if key in STYLE_BLACKLIST:
                message = _("Style includes a non-style related parameter, {}")
                logging.warning(message.format(key))
            elif key in style:
                message = _("Duplicate key in file {}, on line {}")
                logging.warning(message.format(filename, line_number))
            else:
                try:
                    style[key] = value
                except KeyError:
                    message = _("Bad value in file {} on line {}")
                    logging.exception(
                        message.format(filename, line_number))
    except UnicodeDecodeError:
        logging.exception(_("Could not parse {}").format(filename))
    style.name = Path(filename).stem
    return style


WRITE_IGNORELIST = [
    "axes.prop_cycle", "lines.dashdot_pattern", "lines.dashed_pattern",
    "lines.dotted_pattern", "lines.dash_capstyle", "lines.dash_joinstyle",
    "lines.solid_capstyle", "lines.solid_joinstyle",
]


def write_style(file, style):
    stream = _get_write_stream(file)
    _write_string(stream, f"# {style.name}\n")
    _write_string(
        stream,
        f"axes.prop_cycle: {str(style['axes.prop_cycle']).replace('#', '')}\n")
    for key, value in style.items():
        if key not in STYLE_BLACKLIST and key not in WRITE_IGNORELIST:
            value = str(value).replace("#", "")
            value = value.replace("[", "").replace("]", "")
            value = value.replace("'", "").replace("'", "")
            value = value.replace('"', "").replace('"', "")
            line = f"{key}: {value}\n"
            _write_string(stream, line)
    stream.close()


def parse_json(file):
    return json.loads(file.load_bytes(None)[0].get_data())


def write_json(file, json_object, pretty_print=True):
    stream = _get_write_stream(file)
    _write_string(stream, json.dumps(
        json_object, indent=4 if pretty_print else None, sort_keys=True,
    ))
    stream.close()


def parse_xml(file):
    return minidom.parseString(read_file(file))


def _get_write_stream(file):
    if file.query_exists(None):
        return file.replace(None, False, 0, None)
    return file.create(0, None)


def _write_string(stream, line, encoding="utf-8"):
    stream.write_bytes(GLib.Bytes(line.encode(encoding)), None)


def read_file(file, encoding="utf-8"):
    content = file.load_bytes(None)[0].get_data()
    return content if encoding is None else content.decode(encoding)
