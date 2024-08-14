# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
import logging
import sys
from gettext import gettext as _

from gi.repository import Graphs

import gio_pyio

from graphs import utilities
from graphs.figure_settings import FigureSettingsDialog
from graphs.item import DataItem

import numexpr

import numpy


def on_action_invoked(application: Graphs.Application, name: str) -> None:
    """Handle action invokation."""
    getattr(sys.modules[__name__], name + "_action")(application)


def add_equation_action(application: Graphs.Application) -> None:
    """Add data from an equation."""

    def on_accept(_dialog, name):
        settings = application.get_settings_child("add-equation")
        try:
            x_start = utilities.string_to_float(settings.get_string("x-start"))
            x_stop = utilities.string_to_float(settings.get_string("x-stop"))
            step_size = utilities.string_to_float(
                settings.get_string("step-size"),
            )
            datapoints = int(abs(x_start - x_stop) / step_size) + 1
            xdata = numpy.ndarray.tolist(
                numpy.linspace(x_start, x_stop, datapoints),
            )
            equation = utilities.preprocess(settings.get_string("equation"))
            ydata = numpy.ndarray.tolist(
                numexpr.evaluate(equation + " + x*0", local_dict={"x": xdata}),
            )
            if name == "":
                name = f"Y = {settings.get_string('equation')}"
            style_manager = application.get_figure_style_manager()
            application.get_data().add_items(
                [
                    DataItem.new(
                        style_manager.get_selected_style_params(),
                        xdata,
                        ydata,
                        name=name,
                    ),
                ],
                style_manager,
            )
            return ""
        except ValueError as error:
            return str(error)
        except (NameError, SyntaxError, TypeError, KeyError) as exception:
            message = _("{error} - Unable to add data from equation")
            msg = message.format(error=exception.__class__.__name__)
            logging.exception(msg)
            return msg

    dialog = Graphs.AddEquationDialog.new(application)
    dialog.connect("accept", on_accept)


def export_figure_action(application: Graphs.Application) -> None:
    """Export Figure."""

    def on_accept(_dialog, file):
        window = application.get_window()
        settings = application.get_settings_child("export-figure")
        with gio_pyio.open(file, "wb") as wrapper:
            window.get_canvas().figure.savefig(
                wrapper,
                format=settings.get_string("file-format"),
                dpi=settings.get_int("dpi"),
                transparent=settings.get_boolean("transparent"),
            )
        window.add_toast_string_with_file(_("Exported Figure"), file)

    dialog = Graphs.ExportFigureDialog.new(application)
    dialog.connect("accept", on_accept)


def zoom_in_action(application: Graphs.Application) -> None:
    """Zoom into the figure."""
    canvas = application.get_window().get_canvas()
    canvas.zoom(1.15, respect_mouse=False)


def zoom_out_action(application: Graphs.Application) -> None:
    """Zoom out of the figure."""
    canvas = application.get_window().get_canvas()
    canvas.zoom(1 / 1.15, respect_mouse=False)


def figure_settings_action(application: Graphs.Application) -> None:
    """Open Figure Settings Dialog."""
    FigureSettingsDialog(application)
