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
    operation = target.get_string()
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
        figure_settings = self.get_figure_settings()
        args += [
            figure_settings.get_left_scale(),
            figure_settings.get_right_scale(),
            self.get_data().get_items(),
        ]
    elif "translate" in operation or "multiply" in operation:
        window = self.get_window()
        try:
            args += [utilities.string_to_float(
                getattr(window, operation + "_entry").get_text(),
            )]
        except ValueError as error:
            window.add_toast(error)
            return
    operations.perform_operation(
        self, getattr(operations, target.get_string()), *args,
    )


def toggle_sidebar(_action, _shortcut, self):
    flap = self.get_window().sidebar_flap
    flap.set_reveal_flap(not flap.get_reveal_flap())


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
    for item in self.get_data():
        item.selected = True
    self.get_clipboard().add()


def select_none_action(_action, _target, self):
    for item in self.get_data():
        item.selected = False
    self.get_clipboard().add()


def undo_action(_action, _target, self):
    self.get_clipboard().undo()


def redo_action(_action, _target, self):
    self.get_clipboard().redo()


def optimize_limits_action(_action, _target, self):
    utilities.optimize_limits(self)


def view_back_action(_action, _target, self):
    if self.get_window().view_back_button.get_sensitive():
        self.get_view_clipboard().undo()


def view_forward_action(_action, _target, self):
    if self.get_window().view_forward_button.get_sensitive():
        self.get_view_clipboard().redo()


def export_data_action(_action, _target, self):
    ui.export_data_dialog(self)


def export_figure_action(_action, _target, self):
    ExportFigureWindow(self)


def styles_action(_action, _target, self):
    StylesWindow(self)


def save_project_action(_action, _target, self):
    ui.save_project_dialog(self)


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
    items = [item for item in self.get_data() if item.selected]
    names = ", ".join([item.name for item in items])
    self.get_data().delete_items(items)
    self.get_window().add_toast(_("Deleted {}").format(names))
