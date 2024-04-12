# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing and writing styles."""
import logging
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs import file_io

from matplotlib import RcParams, cbook
from matplotlib.font_manager import font_scalings, weight_dict
from matplotlib.style.core import STYLE_BLACKLIST

STYLE_IGNORELIST = [
    "savefig.dpi",
    "savefig.facecolor",
    "savefig.edgecolor",
    "savefig.format",
    "savefix.bbox",
    "savefig.pad_inches",
    "savefig.transparent",
    "savefig.orientation",
]
FONT_SIZE_KEYS = [
    "font.size",
    "axes.labelsize",
    "xtick.labelsize",
    "ytick.labelsize",
    "legend.fontsize",
    "figure.labelsize",
    "figure.titlesize",
    "axes.titlesize",
]


def parse(file: Gio.File) -> (RcParams, str):
    """
    Parse a style to RcParams.

    This is an improved version of matplotlibs '_rc_params_in_file()' function.
    It is also modified to work with GFile instead of the python builtin
    functions.
    """
    style = RcParams()
    filename = Graphs.tools_get_filename(file)
    try:
        stream = Gio.DataInputStream.new(file.read(None))
        for line_number, line in \
                enumerate(file_io.iter_data_stream(stream), 1):
            if line_number == 2:
                name = line[2:]
            line = cbook._strip_comment(line)
            if not line:
                continue
            try:
                key, value = line.split(":", 1)
            except ValueError:
                msg = _("Missing colon in file {file}, line {line}")
                logging.warning(msg.format(file=filename, line=line_number))
                continue
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]  # strip double quotes
            if key in STYLE_BLACKLIST:
                msg = _("Non-style related parameter {param} in file {file}")
                logging.warning(msg.format(param=key, file=filename))
            elif key in STYLE_IGNORELIST:
                msg = _("Ignoring parameter {param} in file {file}")
                logging.warning(msg.format(param=key, file=filename))
            elif key in style:
                msg = _("Duplicate key in file {file}, on line {line}")
                logging.warning(msg.format(file=filename, line=line_number))
            else:
                if key in FONT_SIZE_KEYS \
                        and not value.replace(".", "", 1).isdigit():
                    try:
                        value = font_scalings[value]
                    except KeyError:
                        continue
                elif key == "font.weight" and not value.isdigit():
                    try:
                        value = weight_dict[value]
                    except KeyError:
                        continue
                try:
                    style[key] = value
                except (KeyError, ValueError):
                    msg = _("Bad value in file {file} on line {line}")
                    logging.exception(
                        msg.format(file=filename, line=line_number),
                    )
    except UnicodeDecodeError:
        logging.exception(
            _("Could not parse {filename}").format(filename=filename),
        )
    finally:
        stream.close()
    return style, name


WRITE_IGNORELIST = STYLE_IGNORELIST + [
    "lines.dashdot_pattern",
    "lines.dashed_pattern",
    "lines.dotted_pattern",
    "lines.dash_capstyle",
    "lines.dash_joinstyle",
    "lines.solid_capstyle",
    "lines.solid_joinstyle",
]


def write(file: Gio.File, name: str, style: RcParams) -> None:
    """Write a style to a file."""
    stream = Gio.DataOutputStream.new(file_io.create_write_stream(file))
    stream.put_string("# Generated via Graphs\n")
    stream.put_string(f"# {name}\n")
    for key, value in style.items():
        if key not in STYLE_BLACKLIST and key not in WRITE_IGNORELIST:
            value = str(value).replace("#", "")
            if key != "axes.prop_cycle":
                value = value.replace("[", "").replace("]", "")
                value = value.replace("'", "").replace("'", "")
                value = value.replace('"', "").replace('"', "")
            stream.put_string(f"{key}: {value}\n")
    stream.close()
