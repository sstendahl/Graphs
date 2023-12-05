# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs import operations, ui, utilities
from graphs.add_equation import AddEquationWindow
from graphs.export_figure import ExportFigureWindow
from graphs.data import Data
from graphs.figure_settings import FigureSettingsWindow
from graphs.transform_data import TransformWindow


def perform_operation(_action, target, self):
    operation = target.get_string().removesuffix("_button")
    if operation in ("combine", ):
        return getattr(operations, operation)(self)
    elif operation == "custom_transformation":
        return TransformWindow(self)
    elif operation == "cut" and self.get_mode() != 2:
        return
    args = []
    actions_settings = self.get_settings_child("actions")
    if operation in ("center", "smoothen"):
        args = [actions_settings.get_enum(operation)]
    if operation == "smoothen":
        params = {}
        settings = actions_settings.get_child("smoothen")
        for setting in settings:
            params[setting] = int(settings.get_int(setting))
        args += [params]
    elif operation == "shift":
        figure_settings = self.get_data().get_figure_settings()
        right_range = (figure_settings.get_max_right()
                       - figure_settings.get_min_right())
        left_range = (figure_settings.get_max_left()
                      - figure_settings.get_min_left())
        args += [
            figure_settings.get_left_scale(),
            figure_settings.get_right_scale(),
            self.get_data().get_items(),
            [left_range, right_range],
        ]
    elif "translate" in operation or "multiply" in operation:
        window = self.get_window()
        try:
            args += [utilities.string_to_float(
                window.get_property(operation + "_entry").get_text(),
            )]
        except ValueError as error:
            window.add_toast_string(error)
            return
    operations.perform_operation(self, getattr(operations, operation), *args)


def toggle_sidebar(_action, _shortcut, self):
    split_view = self.get_window().get_split_view()
    split_view.set_collapsed(not split_view.get_collapsed())


def change_scale(action, target, self):
    data = self.get_data()
    data.get_figure_settings().set_property(
        action.get_name()[7:], int(target.get_string()),
    )
    self.get_window().get_canvas().get_parent().grab_focus()
    data.add_history_state()


def set_mode(_action, _target, self, mode):
    self.set_mode(mode)


def quit_action(_action, _target, self):
    self.close_application()


def about_action(_action, _target, self):
    ui.show_about_window(self)


def figure_settings_action(_action, _target, self):
    FigureSettingsWindow(self)


def add_data_action(_action, _target, self):
    ui.add_data_dialog(self)


def add_equation_action(_action, _target, self):
    AddEquationWindow(self)


def select_all_action(_action, _target, self):
    data = self.get_data()
    for item in data:
        item.set_selected(True)
    data.add_history_state()


def select_none_action(_action, _target, self):
    data = self.get_data()
    for item in data:
        item.set_selected(False)
    data.add_history_state()


def undo_action(_action, _target, self):
    self.get_data().undo()


def redo_action(_action, _target, self):
    self.get_data().redo()


def optimize_limits_action(_action, _target, self):
    self.get_data().optimize_limits()


def view_back_action(_action, _target, self):
    data = self.get_data()
    if data.props.can_view_back:
        data.view_back()


def view_forward_action(_action, _target, self):
    data = self.get_data()
    if data.props.can_view_forward:
        data.view_forward()


def export_data_action(_action, _target, self):
    ui.export_data_dialog(self)


def export_figure_action(_action, _target, self):
    ExportFigureWindow(self)


def new_project_action(_action, _target, self):
    # Load default figure settings, close all data, reset clipboard
    # Basical
    if self.get_data().props.unsaved:
        def on_response(_dialog, response):
            if response == "discard_close":
                reset(self)
            if response == "save_close":
                ui.save_project_dialog(self)
                reset(self)


        dialog = ui.build_dialog("close_application")
        dialog.set_transient_for(self.get_window())
        dialog.connect("response", on_response)
        dialog.present()

    def reset(self):
        items = [item for item in self.get_data()]
        names = ", ".join(item.get_name() for item in items)
        self.get_data().delete_items(items)
        settings = self.get_settings()
        figure_settings = Graphs.FigureSettings.new(
            settings.get_child("figure"),
        )
        self.get_data().set_figure_settings(figure_settings)
        self.get_data().props.can_redo = False
        self.get_data().props.can_undo = False
        self.get_data().props.can_view_forward = False
        self.get_data().props.can_view_back = False
        self.get_data().initialize()
        self.get_window().get_content_title().set_title(_("Untitled Project"))


def save_project_action(_action, _target, self):
    ui.save_project_dialog(self)


def save_project_as_action(_action, _target, self):
    ui.save_project_dialog(self, require_dialog=True)


def smoothen_settings_action(_action, _target, self):
    Graphs.SmoothenWindow.new(self)


def zoom_in_action(_action, _target, self):
    canvas = self.get_window().get_canvas()
    canvas.zoom(1.15, respect_mouse=False)


def zoom_out_action(_action, _target, self):
    canvas = self.get_window().get_canvas()
    canvas.zoom(1 / 1.15, respect_mouse=False)


def open_project_action(_action, _target, self):
    if not self.get_data().props.empty:

        def on_response(_dialog, response):
            if response == "discard":
                ui.open_project_dialog(self)

        dialog = ui.build_dialog("discard_data")
        dialog.set_transient_for(self.get_window())
        dialog.connect("response", on_response)
        dialog.present()
        return
    ui.open_project_dialog(self)


def delete_selected_action(_action, _target, self):
    items = [item for item in self.get_data() if item.get_selected()]
    names = ", ".join(item.get_name() for item in items)
    self.get_data().delete_items(items)
    self.get_window().add_toast_string(_("Deleted {}").format(names))
