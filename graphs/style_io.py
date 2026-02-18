# SPDX-License-Identifier: GPL-3.0-or-later
"""
Module for parsing and writing styles.

This module is intended to be used at build time and thus must not depend on
other graphs modules.
"""
import logging
import typing
from gettext import gettext as _
from typing import Tuple

from gi.repository import Gio

from matplotlib import RcParams, cbook, rc_context
from matplotlib.figure import Figure
from matplotlib.font_manager import font_scalings, weight_dict
from matplotlib.style.core import STYLE_BLACKLIST

import numpy

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

STYLE_CUSTOM_PARAMS = [
    "name",
    "ticklabels",
    "errorbar.capsize",
    "errorbar.capthick",
    "errorbar.linewidth",
    "errorbar.barsabove",
    "errorbar.ecolor",
]


class StyleParseError(Exception):
    """Custom Error for when a style cannot be parsed."""


def parse(
    file: Gio.File,
    validate: Tuple[RcParams, dict] = None,
) -> (RcParams, dict):
    """
    Parse a style to RcParams.

    This is an improved version of matplotlibs '_rc_params_in_file()' function.
    It is also modified to work with GFile instead of the python builtin
    functions.
    """

    def _apply_defaults(
        target_dict: dict | RcParams,
        defaults: dict,
        filename,
    ) -> None:
        for key, value in defaults.items():
            if key not in target_dict:
                msg = (
                    "Parameter {key} not found in {filename}, using"
                    " default value: {value}"
                )
                msg = msg.format(key=key, filename=filename, value=value)
                logging.debug(msg)
                target_dict[key] = value

    style = RcParams()
    graphs_params = {"name": None}
    filename = file.get_basename()
    try:
        stream = Gio.DataInputStream.new(file.read(None))
        for line_number, line in enumerate(stream, 1):
            if line[:9] == "#~graphs ":
                graphs_param = True
                line = line[9:]
            else:
                graphs_param = False
                line = cbook._strip_comment(line)
            # legacy support for names at second line
            if line_number == 2 and graphs_params["name"] is None \
                    and line[:2] == "# ":
                graphs_params["name"] = line[2:]
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
            elif key != "name" and \
                    key in (graphs_params if graphs_param else style):
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
                    if graphs_param:
                        if key not in STYLE_CUSTOM_PARAMS:
                            msg = _(
                                "Bad value in file {file} on line {line},"
                                " custom parameter {key} is not supported",
                            )
                            logging.warning(
                                msg.format(
                                    file=filename,
                                    line=line_number,
                                    key=key,
                                ),
                            )
                            continue
                        # Convert boolean-strings to boolean:
                        bool_mapping = {"false": False, "true": True}
                        value = bool_mapping.get(value.lower(), value)
                        floats = \
                            ("errorbar.capsize",
                             "errorbar.capthick",
                             "errorbar.linewidth")
                        if key in floats:
                            value = float(value)
                        graphs_params[key] = value
                    else:
                        style[key] = value
                except (KeyError, ValueError):
                    msg = _("Bad value in file {file} on line {line}")
                    logging.warning(
                        msg.format(file=filename, line=line_number),
                    )
    except UnicodeDecodeError as error:
        msg = _("Could not parse {filename}").format(filename=filename)
        raise StyleParseError(msg) from error
    finally:
        stream.close()
    if validate is not None:
        style_defaults, graph_defaults = validate
        _apply_defaults(style, style_defaults, filename)
        _apply_defaults(graphs_params, graph_defaults, filename)

    if graphs_params["name"] is None:
        msg = _("File {file}, does not contain name tag")
        logging.warning(msg.format(file=filename))
        graphs_params["name"] = filename
    return style, graphs_params


WRITE_IGNORELIST = STYLE_IGNORELIST + [
    "lines.dashdot_pattern",
    "lines.dashed_pattern",
    "lines.dotted_pattern",
    "lines.dash_capstyle",
    "lines.dash_joinstyle",
    "lines.solid_capstyle",
    "lines.solid_joinstyle",
]


def write(file: Gio.File, style: RcParams, graphs_params: dict) -> None:
    """Write a style to a file."""
    stream = Gio.DataOutputStream.new(file.replace(None, False, 0, None))
    stream.put_string("# Generated via Graphs\n")
    for key, value in graphs_params.items():
        stream.put_string(f"#~graphs {key}: {value}\n")
    for key, value in style.items():
        if key not in STYLE_BLACKLIST and key not in WRITE_IGNORELIST:
            value = str(value).replace("#", "")
            if key != "axes.prop_cycle":
                value = value.replace("[", "").replace("]", "")
                value = value.replace("'", "").replace("'", "")
                value = value.replace('"', "").replace('"', "")
            stream.put_string(f"{key}: {value}\n")
    stream.close()


_PREVIEW_XDATA = numpy.linspace(0, 10, 30)
_PREVIEW_YDATA1 = numpy.sin(_PREVIEW_XDATA)
_PREVIEW_YDATA2 = numpy.cos(_PREVIEW_XDATA)


def create_preview(
    file: typing.IO,
    params: Tuple[RcParams, dict],
    file_format: str = "svg",
    dpi: int = 100,
) -> None:
    """Create preview of params and write it to file."""
    style_params, graphs_params = params
    with rc_context(style_params):
        # set render size in inch
        figure = Figure(figsize=(5, 3))
        axis = figure.add_subplot()
        axis.spines.bottom.set_visible(True)
        axis.spines.left.set_visible(True)
        if style_params["axes.spines.top"] and graphs_params["ticklabels"]:
            tick_params = {
                "labelleft": style_params["ytick.left"],
                "labelright": style_params["ytick.right"],
                "labeltop": style_params["xtick.top"],
                "labelbottom": style_params["xtick.bottom"],
            }
            axis.tick_params(which="both", **tick_params)
        else:
            axis.tick_params(which="both", top=False, right=False)
        axis.plot(_PREVIEW_XDATA, _PREVIEW_YDATA1)
        axis.plot(_PREVIEW_XDATA, _PREVIEW_YDATA2)
        axis.set_xlabel(_("X Label"))
        axis.set_xlabel(_("Y Label"))
        figure.savefig(file, format=file_format, dpi=dpi)
