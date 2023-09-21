# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
from gettext import gettext as _

from gi.repository import Graphs

from graphs import operations, ui, utilities
from graphs.add_equation import AddEquationWindow
from graphs.export_figure import ExportFigureWindow
from graphs.figure_settings import FigureSettingsWindow
from graphs.styles import StylesWindow
from graphs.transform_data import TransformWindow


def perform_operation(_action, target, self):
    operation = target.get_string().lower().replace(" ", "_")
    if operation == "combine":
        return operations.combine(self)
    elif operation == "custom_transformation":
        return TransformWindow(self)
    elif operation == "cut" and self.get_mode() != 2:
        return
    args = []
    if operation in ["center"]:
        args = [self.get_settings("general").get_enum(operation)]
    if operation == "shift":
        figure_settings = self.get_data().get_figure_settings()
        args += [
            figure_settings.get_left_scale(),
            figure_settings.get_right_scale(),
            self.get_data().get_items(),
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


def set_mode(_action, _target, self, mode):
    self.set_mode(mode)


def quit_action(_action, _target, self):
    self.quit()


def about_action(_action, _target, self):
    ui.show_about_window(self)


def preferences_action(_action, _target, self):
    Graphs.PreferencesWindow.new(self)


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


def styles_action(_action, _target, self):
    StylesWindow(self)


def save_project_action(_action, _target, self):
    ui.save_project_dialog(self)


def zoom_in_action(_action, _target, self):
    canvas = self.get_window().get_canvas()
    canvas.xfrac, canvas.yfrac = 0.5, 0.5
    canvas.zoom(1.15)


def zoom_out_action(_action, _target, self):
    canvas = self.get_window().get_canvas()
    canvas.xfrac, canvas.yfrac = 0.5, 0.5
    canvas.zoom(1 / 1.15)


def open_project_action(_action, _target, self):
    if not self.get_data().is_empty():
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
    names = ", ".join([item.get_name() for item in items])
    self.get_data().delete_items(items)
    self.get_window().add_toast_string(_("Deleted {}").format(names))
