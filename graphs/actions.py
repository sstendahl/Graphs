# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
from gettext import gettext as _

from gi.repository import Adw, GLib, Gio, Graphs, Gtk

from graphs import file_io, operations, ui, utilities
from graphs.add_equation import AddEquationDialog
from graphs.export_figure import ExportFigureDialog
from graphs.figure_settings import FigureSettingsDialog
from graphs.transform_data import TransformDialog


def perform_operation(
    _action,
    target: GLib.Variant,
    application: Graphs.Application,
):
    operation = target.get_string().removesuffix("_button")
    if operation in ("combine", ):
        return getattr(operations, operation)(application)
    elif operation == "custom_transformation":
        return TransformDialog(application)
    elif operation == "cut" and application.get_mode() != 2:
        return
    args = []
    actions_settings = application.get_settings_child("actions")
    if operation in ("center", "smoothen"):
        args = [actions_settings.get_enum(operation)]
    if operation == "smoothen":
        params = {}
        settings = actions_settings.get_child("smoothen")
        for setting in settings:
            params[setting] = int(settings.get_int(setting))
        args += [params]
    elif operation == "shift":
        figure_settings = application.get_data().get_figure_settings()
        right_range = (
            figure_settings.get_max_right() - figure_settings.get_min_right()
        )
        left_range = (
            figure_settings.get_max_left() - figure_settings.get_min_left()
        )
        args += [
            figure_settings.get_left_scale(),
            figure_settings.get_right_scale(),
            application.get_data().get_items(),
            [left_range, right_range],
        ]
    elif "translate" in operation or "multiply" in operation:
        window = application.get_window()
        try:
            args += [
                utilities.string_to_float(
                    window.get_property(operation + "_entry").get_text(),
                ),
            ]
        except ValueError as error:
            window.add_toast_string(str(error))
            return
    operations.perform_operation(
        application,
        getattr(operations, operation),
        *args,
    )


def toggle_sidebar(
    _action,
    _shortcut,
    application: Graphs.Application,
) -> None:
    split_view = application.get_window().get_split_view()
    split_view.set_collapsed(not split_view.get_collapsed())


def change_scale(
    action: Gio.Action,
    target: GLib.Variant,
    application: Graphs.Application,
) -> None:
    data = application.get_data()
    visible_axes = data.get_used_positions()
    direction = action.get_name()[7:-6]
    directions = [direction]
    # Also set opposite axis if opposite axis not in use
    if direction in ["top", "bottom"] and visible_axes[0] ^ visible_axes[1]:
        directions = ["top", "bottom"]
    elif direction in ["left", "right"] and visible_axes[2] ^ visible_axes[3]:
        directions = ["left", "right"]
    for direction in directions:
        data.get_figure_settings().set_property(
            f"{direction}-scale",
            int(target.get_string()),
        )
    application.get_window().get_canvas().get_parent().grab_focus()
    data.add_history_state()


def set_mode(
    _action,
    _target,
    application: Graphs.Application,
    mode: str,
) -> None:
    application.set_mode(mode)


def quit_action(_action, _target, application: Graphs.Application) -> None:
    application.close_application()


def about_action(_action, _target, application: Graphs.Application) -> None:
    ui.show_about_dialog(application)


def figure_settings_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    FigureSettingsDialog(application)


def add_data_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    ui.add_data_dialog(application)


def add_equation_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    AddEquationDialog(application)


def select_all_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    data = application.get_data()
    for item in data:
        item.set_selected(True)
    data.add_history_state()


def select_none_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    data = application.get_data()
    for item in data:
        item.set_selected(False)
    data.add_history_state()


def undo_action(_action, _target, application: Graphs.Application) -> None:
    application.get_data().undo()


def redo_action(_action, _target, application: Graphs.Application) -> None:
    application.get_data().redo()


def optimize_limits_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    application.get_data().optimize_limits()


def view_back_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    data = application.get_data()
    if data.props.can_view_back:
        data.view_back()


def view_forward_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    data = application.get_data()
    if data.props.can_view_forward:
        data.view_forward()


def export_data_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    ui.export_data_dialog(application)


def export_figure_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    ExportFigureDialog(application)


def new_project_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    """Clear the current project and reset Graphs to the initial state"""
    if application.get_data().props.unsaved:

        def on_response(_dialog, response):
            application.save_handler = application.connect(
                "project-saved",
                application.on_project_saved,
                "reset_project",
            )
            if response == "discard_close":
                application.get_data().reset_project()
            if response == "save_close":
                file_io.save_project(application)

        dialog = ui.build_dialog("save_changes")
        dialog.set_transient_for(application.get_window())
        dialog.connect("response", on_response)
        dialog.present()
        return
    application.get_data().reset_project()


def save_project_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    file_io.save_project(application)


def save_project_as_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    file_io.save_project(application, require_dialog=True)


def smoothen_settings_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    Graphs.SmoothenDialog.new(application)


def zoom_in_action(_action, _target, application: Graphs.Application) -> None:
    canvas = application.get_window().get_canvas()
    canvas.zoom(1.15, respect_mouse=False)


def zoom_out_action(_action, _target, application: Graphs.Application) -> None:
    canvas = application.get_window().get_canvas()
    canvas.zoom(1 / 1.15, respect_mouse=False)


def open_project_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    if application.get_data().props.unsaved:

        def on_response(_dialog, response):
            if response == "discard_close":
                ui.open_project_dialog(application)
            if response == "save_close":
                # Retrieving open dialog first means that save dialog will be
                # on top. Thus user will be presented with save dialog first.
                ui.open_project_dialog(application)
                file_io.save_project(application)

        dialog = ui.build_dialog("save_changes")
        dialog.set_transient_for(application.get_window())
        dialog.connect("response", on_response)
        dialog.present()
        return
    ui.open_project_dialog(application)


def delete_selected_action(
    _action,
    _target,
    application: Graphs.Application,
) -> None:
    items = [item for item in application.get_data() if item.get_selected()]
    names = ", ".join(item.get_name() for item in items)
    application.get_data().delete_items(items)
    toast = Adw.Toast.new(_("Deleted {name}").format(name=names))
    toast.set_button_label("Undo")
    toast.set_action_name("app.undo")
    application.get_window().add_toast(toast)


def open_file_location(_action, _target, file: Gio.File) -> None:
    """Open and select `file` in the file manager"""
    file_launcher = Gtk.FileLauncher.new(file)
    file_launcher.open_containing_folder()
