# SPDX-License-Identifier: GPL-3.0-or-later
import json
import logging
from gettext import gettext as _
from pathlib import Path
from xml.dom import minidom

from gi.repository import GLib

from graphs import utilities

from matplotlib import RcParams, cbook
from matplotlib.style.core import STYLE_BLACKLIST

import numpy


def save_item(file, item_):
    delimiter = "\t"
    fmt = delimiter.join(["%.12e"] * 2)
    stream = get_write_stream(file)
    if item_.xlabel != "" and item_.ylabel != "":
        _write_string(stream, item_.xlabel + delimiter + item_.ylabel + "\n")
    for row in numpy.stack([item_.xdata, item_.ydata], axis=1):
        _write_string(stream, fmt % tuple(row) + "\n")
    stream.close()


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
    stream = get_write_stream(file)
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
    stream = get_write_stream(file)
    _write_string(stream, json.dumps(
        json_object, indent=4 if pretty_print else None, sort_keys=True,
    ))
    stream.close()


def parse_xml(file):
    return minidom.parseString(read_file(file))


def get_write_stream(file):
    if file.query_exists(None):
        return file.replace(None, False, 0, None)
    return file.create(0, None)


def _write_string(stream, line, encoding="utf-8"):
    stream.write_bytes(GLib.Bytes(line.encode(encoding)), None)


def read_file(file, encoding="utf-8"):
    content = file.load_bytes(None)[0].get_data()
    return content if encoding is None else content.decode(encoding)
