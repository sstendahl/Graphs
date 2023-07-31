# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
from graphs import graphs, plotting_tools, ui
from graphs.add_equation import AddEquationWindow
from graphs.export_figure import ExportFigureWindow
from graphs.plot_settings import PlotSettingsWindow
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


def plot_settings_action(_action, _target, self):
    PlotSettingsWindow(self)


def add_data_action(_action, _target, self):
    ui.add_data_dialog(self)


def add_equation_action(_action, _target, self):
    AddEquationWindow(self)


def select_all_action(_action, _target, self):
    if not self.datadict:
        return
    for item in self.datadict.values():
        item.selected = True
    graphs.refresh(self)
    ui.reload_item_menu(self)
    ui.enable_data_dependent_buttons(self)


def select_none_action(_action, _target, self):
    if not self.datadict:
        return
    for item in self.datadict.values():
        item.selected = False
    graphs.refresh(self)
    ui.reload_item_menu(self)
    ui.enable_data_dependent_buttons(self)


def undo_action(_action, _target, self):
    self.Clipboard.undo()


def redo_action(_action, _target, self):
    self.Clipboard.redo()


def optimize_limits_action(_action, _target, self):
    plotting_tools.optimize_limits(self)
    graphs.refresh(self)


def view_back_action(_action, _target, self):
    if self.canvas.toolbar.back_enabled:
        self.canvas.toolbar.back()
        self.canvas.apply_limits()
        # Fix weird view on back
        graphs.refresh(self)


def view_forward_action(_action, _target, self):
    if self.canvas.toolbar.forward_enabled:
        self.canvas.toolbar.forward()
        self.canvas.apply_limits()


def export_data_action(_action, _target, self):
    ui.export_data_dialog(self)


def export_figure_action(_action, _target, self):
    ExportFigureWindow(self)


def plot_styles_action(_action, _target, self):
    PlotStylesWindow(self)


def save_project_action(_action, _target, self):
    ui.save_project_dialog(self)


def open_project_action(_action, _target, self):
    if len(self.datadict) > 0:
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
    for item in self.datadict.copy().values():
        if item.selected:
            graphs.delete_item(self, item.key, True)
