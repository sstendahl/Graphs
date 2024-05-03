# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for saving and loading projects."""
import contextlib
from gettext import gettext as _

from gi.repository import GLib, Gio, Graphs, Gtk

from graphs import file_io, migrate, misc, utilities


def read_project_file(file: Gio.File) -> dict:
    """Read a project dict from file and account for migration."""
    try:
        project_dict = file_io.parse_json(file)
    except UnicodeDecodeError:
        project_dict = migrate.migrate_project(file)
    return project_dict


def save_project_dict(file: Gio.File, project_dict: dict) -> None:
    """Save a project dict to a file."""
    file_io.write_json(file, project_dict)


_GRAPHS_PROJECT_FILE_ONLY_FILE_FILTER = utilities.create_file_filters(
    (misc.GRAPHS_PROJECT_FILE_FILTER_TEMPLATE, ),
)


def open_project(application: Graphs.Application) -> None:
    """Open a project."""

    def pick_file():

        def on_pick_response(dialog, response):
            with contextlib.suppress(GLib.GError):
                data = application.get_data()
                data.set_file(dialog.open_finish(response))
                data.load()

        dialog = Gtk.FileDialog()
        dialog.set_filters(_GRAPHS_PROJECT_FILE_ONLY_FILE_FILTER)
        dialog.open(application.get_window(), None, on_pick_response)

    if not application.get_data().get_unsaved():
        pick_file()
        return

    def on_save_response(_dialog, response):
        if response == "discard_close":
            pick_file()
        if response == "save_close":
            # Retrieving open dialog first means that save dialog will be
            # on top. Thus user will be presented with save dialog first.
            pick_file()
            save_project(application)

    dialog = Graphs.tools_build_dialog("save_changes")
    dialog.connect("response", on_save_response)
    dialog.present(application.get_window())
