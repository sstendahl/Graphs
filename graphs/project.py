# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for saving and loading projects."""
import contextlib
from gettext import gettext as _

from gi.repository import Adw, GLib, Gio, Graphs, Gtk

from graphs import actions, file_io, migrate, misc, utilities


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


def _save(application: Graphs.Application) -> None:
    data = application.get_data()
    project_file = data.props.file
    project_dict = data.get_project_dict(application.get_version())
    save_project_dict(project_file, project_dict)
    data.props.unsaved = False
    data.emit("saved")

    action = Gio.SimpleAction.new(
        "open-file-location",
        None,
    )
    action.connect(
        "activate",
        actions.open_file_location,
        project_file,
    )
    application.add_action(action)
    toast = Adw.Toast.new(_("Saved Project"))
    toast.set_button_label(_("Open Location"))
    toast.set_action_name("app.open-file-location")
    application.get_window().add_toast(toast)


def save_project(
    application: Graphs.Application,
    require_dialog: bool = False,
) -> None:
    """Save the current data to disk."""
    data = application.get_data()
    if data.props.file is not None and not require_dialog:
        _save(application)
        return

    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            data.props.file = dialog.save_finish(response)
            _save(application)

    dialog = Gtk.FileDialog()
    dialog.set_filters(_GRAPHS_PROJECT_FILE_ONLY_FILE_FILTER)
    dialog.set_initial_name(_("Project") + ".graphs")
    dialog.save(application.get_window(), None, on_response)


def open_project(application: Graphs.Application) -> None:
    """Open a project."""

    def pick_file():

        def on_pick_response(dialog, response):
            with contextlib.suppress(GLib.GError):
                load(application.get_data(), dialog.open_finish(response))

        dialog = Gtk.FileDialog()
        dialog.set_filters(_GRAPHS_PROJECT_FILE_ONLY_FILE_FILTER)
        dialog.open(application.get_window(), None, on_pick_response)

    if not application.get_data().props.unsaved:
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


def load(data: Graphs.DataInterface, file: Gio.File) -> None:
    """Load a project from file into data."""
    data.props.file = file
    data.load_from_project_dict(read_project_file(file))
