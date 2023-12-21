# SPDX-License-Identifier: GPL-3.0-or-later
import io
import logging
from gettext import gettext as _

from PIL import Image

import numpy

from gi.repository import Gio

from graphs import file_io, utilities

from matplotlib import RcParams, cbook, rc_context
from matplotlib.backends.backend_gtk4cairo import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.font_manager import font_scalings, weight_dict
from matplotlib.style.core import STYLE_BLACKLIST


STYLE_IGNORELIST = [
    "savefig.dpi", "savefig.facecolor", "savefig.edgecolor", "savefig.format",
    "savefix.bbox", "savefig.pad_inches", "savefig.transparent",
    "savefig.orientation",
]
FONT_SIZE_KEYS = [
    "font.size", "axes.labelsize", "xtick.labelsize", "ytick.labelsize",
    "legend.fontsize", "figure.labelsize", "figure.titlesize",
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
    filename = utilities.get_filename(file)
    try:
        wrapper = file_io.open_wrapped(file, "rt")
        for line_number, line in enumerate(wrapper, 1):
            line = line.strip()
            if line_number == 2:
                name = line[2:]
            line = cbook._strip_comment(line)
            if not line:
                continue
            try:
                key, value = line.split(":", 1)
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
                message = _("Non-style related parameter {} in file {}")
                logging.warning(message.format(key, filename))
            elif key in STYLE_IGNORELIST:
                message = _("Ignoring parameter {} in file {}")
                logging.warning(message.format(key, filename))
            elif key in style:
                message = _("Duplicate key in file {}, on line {}")
                logging.warning(message.format(filename, line_number))
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
                    message = _("Bad value in file {} on line {}")
                    logging.exception(
                        message.format(filename, line_number))
    except UnicodeDecodeError:
        logging.exception(_("Could not parse {}").format(filename))
    finally:
        wrapper.close()
    return style, name


WRITE_IGNORELIST = STYLE_IGNORELIST + [
    "lines.dashdot_pattern", "lines.dashed_pattern",
    "lines.dotted_pattern", "lines.dash_capstyle", "lines.dash_joinstyle",
    "lines.solid_capstyle", "lines.solid_joinstyle",
]


def write(file: Gio.File, name: str, style: RcParams):
    with file_io.open_wrapped(file, "wt") as wrapper:
        wrapper.write("# Generated via Graphs\n")
        wrapper.write(f"# {name}\n")
        for key, value in style.items():
            if key not in STYLE_BLACKLIST and key not in WRITE_IGNORELIST:
                value = str(value).replace("#", "")
                if key != "axes.prop_cycle":
                    value = value.replace("[", "").replace("]", "")
                    value = value.replace("'", "").replace("'", "")
                    value = value.replace('"', "").replace('"', "")
                wrapper.write(f"{key}: {value}\n")


_PREVIEW_XDATA = numpy.linspace(0, 10, 30)
_PREVIEW_YDATA1 = numpy.sin(_PREVIEW_XDATA)
_PREVIEW_YDATA2 = numpy.cos(_PREVIEW_XDATA)


def generate_preview(style: RcParams) -> Gio.File:
    file, stream = Gio.File.new_tmp(None)
    with file_io.FileLikeWrapper.new_for_io_stream(stream) as wrapper, \
            rc_context(style):
        # set render size in inch
        figure = Figure(figsize=(5, 3))
        axis = figure.add_subplot()
        axis.spines.bottom.set_visible(True)
        axis.spines.left.set_visible(True)
        if not style["axes.spines.top"]:
            axis.tick_params(which="both", top=False, right=False)
        axis.plot(_PREVIEW_XDATA, _PREVIEW_YDATA1)
        axis.plot(_PREVIEW_XDATA, _PREVIEW_YDATA2)
        axis.set_xlabel(_("X Label"))
        axis.set_xlabel(_("Y Label"))
        figure.savefig(wrapper, format="svg")
    return file


def generate_system_preview(light_style: RcParams,
                            dark_style: RcParams) -> Gio.File:
    # Generate light variant
    with rc_context(light_style):
        figure = Figure(figsize=(5, 3))
        axis = figure.add_subplot()
        axis.spines.bottom.set_visible(True)
        axis.spines.left.set_visible(True)
        if not light_style["axes.spines.top"]:
            axis.tick_params(which="both", top=False, right=False)
        axis.plot(_PREVIEW_XDATA, _PREVIEW_YDATA1)
        axis.plot(_PREVIEW_XDATA, _PREVIEW_YDATA2)
        axis.set_xlabel(_("X Label"))
        axis.set_ylabel(_("Y Label"))
        canvas = FigureCanvas(figure)
        buf = io.BytesIO()
        canvas.print_figure(buf, format="png")
        buf.seek(0)
        light_img = Image.open(buf)

    # Generate dark variant
    with rc_context(dark_style):
        figure = Figure(figsize=(5, 3))
        axis = figure.add_subplot()
        axis.spines.bottom.set_visible(True)
        axis.spines.left.set_visible(True)
        if not dark_style["axes.spines.top"]:
            axis.tick_params(which="both", top=False, right=False)
        axis.plot(_PREVIEW_XDATA, _PREVIEW_YDATA1)
        axis.plot(_PREVIEW_XDATA, _PREVIEW_YDATA2)
        axis.set_xlabel(_("X Label"))
        axis.set_ylabel(_("Y Label"))
        canvas = FigureCanvas(figure)
        buf = io.BytesIO()
        canvas.print_figure(buf, format="png")
        buf.seek(0)
        dark_img = Image.open(buf)

    # Stitch the images
    stitched_image = stitch_images(light_img, dark_img)

    # Save the stitched image to a Gio.File
    file, stream = Gio.File.new_tmp(None)
    with file_io.FileLikeWrapper.new_for_io_stream(stream) as wrapper:
        stitched_image.save(wrapper, format="png")

    return file


def stitch_images(light_image: Image, dark_image: Image) -> Image:
    # Convert the images to numpy arrays
    light_image = numpy.array(light_image)
    dark_image = numpy.array(dark_image)

    # Cut the images in half
    light_image_half = light_image[:, :light_image.shape[1] // 2]
    dark_image_half = dark_image[:, dark_image.shape[1] // 2:]

    # Concatenate the image halves
    stitched_image = numpy.concatenate(
        (light_image_half, dark_image_half), axis=1)

    # Convert the result back to an image
    return Image.fromarray(stitched_image)
