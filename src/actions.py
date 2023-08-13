# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
from gettext import gettext as _

from graphs import plotting_tools, ui
from graphs.add_equation import AddEquationWindow
from graphs.export_figure import ExportFigureWindow
from graphs.figure_settings import FigureSettingsWindow
from graphs.plot_styles import PlotStylesWindow
from graphs.preferences import PreferencesWindow


def toggle_sidebar(_action, _shortcut, self):
    flap = self.main_window.sidebar_flap
    flap.set_reveal_flap(not flap.get_reveal_flap())


def quit_action(_action, _target, self):
    self.quit()


def about_action(_action, _target, self):
    ui.show_about_window(self)


def preferences_action(_action, _target, self):
    PreferencesWindow(self)


def figure_settings_action(_action, _target, self):
    FigureSettingsWindow(self)


def add_data_action(_action, _target, self):
    ui.add_data_dialog(self)


def add_equation_action(_action, _target, self):
    AddEquationWindow(self)


def select_all_action(_action, _target, self):
    if self.props.data.is_empty():
        return
    for item in self.props.data.props.items:
        item.selected = True
    ui.enable_data_dependent_buttons(self)


def select_none_action(_action, _target, self):
    if self.props.data.is_empty():
        return
    for item in self.props.data.props.items:
        item.selected = False
    ui.enable_data_dependent_buttons(self)


def undo_action(_action, _target, self):
    self.props.clipboard.undo()


def redo_action(_action, _target, self):
    self.props.clipboard.redo()


def optimize_limits_action(_action, _target, self):
    plotting_tools.optimize_limits(self)
    ui.refresh(self)


def view_back_action(_action, _target, self):
    if self.main_window.view_back_button.get_sensitive():
        self.props.view_clipboard.undo()


def view_forward_action(_action, _target, self):
    if self.main_window.view_forward_button.get_sensitive():
        self.props.view_clipboard.redo()


def export_data_action(_action, _target, self):
    ui.export_data_dialog(self)


def export_figure_action(_action, _target, self):
    ExportFigureWindow(self)


def plot_styles_action(_action, _target, self):
    PlotStylesWindow(self)


def save_project_action(_action, _target, self):
    ui.save_project_dialog(self)


def open_project_action(_action, _target, self):
    if not self.props.data.is_empty():
        def on_response(_dialog, response):
            if response == "discard":
                ui.open_project_dialog(self)
        dialog = ui.build_dialog("discard_data")
        dialog.set_transient_for(self.main_window)
        dialog.connect("response", on_response)
        dialog.present()
        return
    ui.open_project_dialog(self)


def delete_selected_action(_action, _target, self):
    items = [item for item in self.props.data.props.items if item.selected]
    names = ", ".join([item.name for item in items])
    self.props.data.delete_items(items)
    self.main_window.add_toast(_("Deleted {}").format(names))
