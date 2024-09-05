# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
import sys
from gettext import gettext as _

from gi.repository import Graphs

import gio_pyio

from graphs.figure_settings import FigureSettingsDialog


def on_action_invoked(application: Graphs.Application, name: str) -> None:
    """Handle action invokation."""
    getattr(sys.modules[__name__], name + "_action")(application)


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
