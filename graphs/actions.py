# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
import contextlib
import logging
import sys
from gettext import gettext as _, pgettext as C_

from gi.repository import GLib, Graphs, Gtk

from graphs import (
    export_data,
    file_import,
    file_io,
    misc,
    project,
    utilities,
)
from graphs.figure_settings import FigureSettingsDialog
from graphs.item import DataItem

import numexpr

import numpy


def on_action_invoked(application: Graphs.Application, name: str) -> None:
    """Handle action invokation."""
    getattr(sys.modules[__name__], name + "_action")(application)


def add_data_action(application: Graphs.Application) -> None:
    """Import data."""

    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            file_import.import_from_files(
                application,
                dialog.open_multiple_finish(response),
            )

    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters((
            (
                C_("file-filter", "Supported files"),
                ["xy", "dat", "txt", "csv", "xrdml", "xry", "graphs"],
            ),
            (C_("file-filter", "ASCII files"), ["xy", "dat", "txt", "csv"]),
            (C_("file-filter", "PANalytical XRDML"), ["xrdml"]),
            (C_("file-filter", "Leybold xry"), ["xry"]),
            misc.GRAPHS_PROJECT_FILE_FILTER_TEMPLATE,
        )),
    )
    dialog.open_multiple(application.get_window(), None, on_response)


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


def export_data_action(application: Graphs.Application) -> None:
    """Export Data."""
    data = application.get_data()
    if data.props.empty:
        application.get_window().add_toast_string(_("No data to export"))
        return
    export_data.export_items(application, data.get_items())


def export_figure_action(application: Graphs.Application) -> None:
    """Export Figure."""

    def on_accept(_dialog, file):
        window = application.get_window()
        settings = application.get_settings_child("export-figure")
        with file_io.open_wrapped(file, "wb") as wrapper:
            window.get_canvas().figure.savefig(
                wrapper,
                format=settings.get_string("file-format"),
                dpi=settings.get_int("dpi"),
                transparent=settings.get_boolean("transparent"),
            )
        window.add_toast_string_with_file(_("Exported Figure"), file)

    dialog = Graphs.ExportFigureDialog.new(application)
    dialog.connect("accept", on_accept)


def new_project_action(application: Graphs.Application) -> None:
    """Clear the current project and reset Graphs to the initial state."""
    data = application.get_data()
    if data.get_unsaved():

        def on_response(_dialog, response):
            application.save_handler = data.connect(
                "saved",
                application.on_project_saved,
                "reset_project",
            )
            if response == "discard_close":
                data.reset()
            if response == "save_close":
                project.save_project(application)

        dialog = Graphs.tools_build_dialog("save_changes")
        dialog.set_transient_for(application.get_window())
        dialog.connect("response", on_response)
        dialog.present()
        return
    data.reset()


def save_project_action(application: Graphs.Application) -> None:
    """Save the current project."""
    project.save_project(application)


def save_project_as_action(application: Graphs.Application) -> None:
    """Save the current project and ask for save location."""
    project.save_project(application, require_dialog=True)


def zoom_in_action(application: Graphs.Application) -> None:
    """Zoom into the figure."""
    canvas = application.get_window().get_canvas()
    canvas.zoom(1.15, respect_mouse=False)


def zoom_out_action(application: Graphs.Application) -> None:
    """Zoom out of the figure."""
    canvas = application.get_window().get_canvas()
    canvas.zoom(1 / 1.15, respect_mouse=False)


def open_project_action(application: Graphs.Application) -> None:
    """Open a project."""
    project.open_project(application)


def figure_settings_action(application: Graphs.Application) -> None:
    """Open Figure Settings Dialog."""
    FigureSettingsDialog(application)
