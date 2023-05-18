# SPDX-License-Identifier: GPL-3.0-or-later
import io
import json
import logging
import pickle
import re
from gettext import gettext as _
from pathlib import Path
from xml.dom import minidom

from gi.repository import GLib

from graphs import utilities
from graphs.item import Item

from matplotlib import RcParams, cbook
from matplotlib.style.core import STYLE_BLACKLIST

import numpy


def save_project(file, plot_settings, datadict, datadict_clipboard,
                 clipboard_pos, version):
    project_data = {
        "plot_settings": plot_settings,
        "data": datadict,
        "datadict_clipboard": datadict_clipboard,
        "clipboard_pos": clipboard_pos,
        "version": version,
    }
    if file.query_exists(None):
        stream = file.replace(None, False, 0, None)
    else:
        stream = file.create(0, None)
    stream.write_bytes(GLib.Bytes(pickle.dumps(project_data)))
    stream.close()


def read_project(file):
    project = pickle.loads(file.load_bytes(None)[0].get_data())
    return \
        project["plot_settings"], project["data"], \
        project["datadict_clipboard"], project["clipboard_pos"], \
        project["version"]


def save_item(file, xdata, ydata):
    array = numpy.stack([xdata, ydata], axis=1)
    fmt = "\t".join(["%.12e"] * 2)
    if file.query_exists(None):
        stream = file.replace(None, False, 0, None)
    else:
        stream = file.create(0, None)
    for row in array:
        line = (fmt % tuple(row) + "\n").encode("utf-8")
        stream.write_bytes(GLib.Bytes(line))
    stream.close()


def import_from_xrdml(self, import_settings):
    file = import_settings.file
    content = minidom.parseString(
        file.load_bytes(None)[0].get_data().decode("utf-8"))
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
    if len(xdata) == 0:
        filename = file.query_info("standard::*", 0, None).get_display_name()
        raise ValueError(_("Unable to retrieve data for {}".format(filename)))

    item = Item(self, xdata, ydata, import_settings.name)
    item.xlabel = f"{scan_axis} ({unit})"
    item.ylabel = _("Intensity (cps)")
    return [item]


def import_from_xry(self, import_settings):
    """
    Import data from .xry files used by Leybold X-ray apparatus.

    Slightly modified version of
    https://github.com/rdbeerman/Readxry/blob/master/manual.py
    """
    file = import_settings.file
    content = file.load_bytes(None)[0].get_data().decode("ISO-8859-1")
    rawdata = [line.strip() for line in content.splitlines()]
    b_min = float(rawdata[4].split()[0])
    b_max = float(rawdata[4].split()[1])

    ydata = numpy.array(rawdata[18:-11]).astype(float)
    xdata = numpy.arange(b_min, b_max, (b_max - b_min) / len(ydata))

    if len(xdata) == 0:
        filename = file.query_info("standard::*", 0, None).get_display_name()
        raise ValueError(_("Unable to retrieve data for {}".format(filename)))

    item = Item(self, xdata, ydata, import_settings.name)
    item.xlabel = _("β (°)")
    item.ylabel = _("Intensity (s⁻¹)")
    return [item]


def import_from_columns(self, import_settings):
    file = import_settings.file
    xdata, ydata = [], []
    xlabel, ylabel = "", ""
    content = file.load_bytes(None)[0].get_data().decode("utf-8")
    params = import_settings.params
    for i, line in enumerate(content.splitlines()):
        if i > params["skip_rows"]:
            line = line.strip()
            data_line = re.split(str(params["delimiter"]), line)
            if params["separator"] == ",":
                for index, value in enumerate(data_line):
                    data_line[index] = utilities.swap(value)
            if utilities.check_if_floats(data_line):
                if len(data_line) == 1:
                    xdata.append(i)
                    ydata.append(float(data_line[0]))
                else:
                    xdata.append(float(data_line[params["column_x"]]))
                    ydata.append(float(data_line[params["column_y"]]))
            # If not all values in the line are floats, start looking for
            # headers instead
            else:
                # By default it will check for headers using at least
                # two whitespaces as delimiter (often tabs), but if
                # that doesn"t work it will try the same delimiter as
                # used for the data import itself The reasoning is that
                # some people use tabs for the headers, but e.g. commas
                # for the data
                try:
                    headers = re.split("\\s{2,}", line)
                    xlabel = headers[params["column_x"]]
                    ylabel = headers[params["column_y"]]
                except IndexError:
                    try:
                        headers = re.split(params.delimiter, line)
                        xlabel = headers[params["column_x"]]
                        ylabel = headers[params["column_y"]]
                    # If neither heuristic works, we just skip headers
                    except IndexError:
                        pass
    if len(xdata) == 0:
        filename = file.query_info("standard::*", 0, None).get_display_name()
        raise ValueError(_("Unable to retrieve data for {}".format(filename)))
    item = Item(self, xdata, ydata, import_settings.name)
    item.xlabel = xlabel
    item.ylabel = ylabel
    return [item]


def parse_style(file):
    """
    Parse a style to RcParams.

    This is an improved version of matplotlibs '_rc_params_in_file()' function.
    It is also modified to work with GFile instead of the python builtin
    functions.
    """
    style = RcParams()
    filename = file.query_info("standard::*", 0, None).get_display_name()
    try:
        content = file.load_bytes(None)[0].get_data().decode("utf-8")
        for line_number, line in enumerate(content.splitlines(), 1):
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
                message = _("Stye includes a non-style related parameter, {}")
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
    "lines.dash_capstyle", "lines.dash_joinstyle", "lines.solid_capstyle",
    "lines.solid_joinstyle",
]


def write_style(file, style):
    stream = file.replace(None, False, 0, None)
    stream.write_bytes(GLib.Bytes(f"# {style.name}\n".encode("utf-8")), None)
    for key, value in style.items():
        if key not in STYLE_BLACKLIST and key not in WRITE_IGNORELIST:
            value = str(value).replace("#", "")
            if value.startswith("[") and value.endswith("]"):
                value = value[1:-1]  # strip lists
            line = f"{key}: {value}\n"
            stream.write_bytes(GLib.Bytes(line.encode("utf-8")), None)
    stream.close()


def parse_json(file):
    return json.loads(file.load_bytes(None)[0].get_data())


def write_json(file, json_object):
    buffer = io.StringIO()
    json.dump(json_object, buffer, indent=4, sort_keys=True)
    stream = file.replace(None, False, 0, None)
    stream.write_bytes(GLib.Bytes(buffer.getvalue().encode("utf-8")), None)
    buffer.close()
    stream.close()
