# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
import logging

from gi.repository import Adw, Gtk

from graphs import clipboard, graphs, operations, ui, utilities
from graphs.add_data_advanced import AddAdvancedWindow
from graphs.add_equation import AddEquationWindow
from graphs.export_figure import ExportFigureWindow
from graphs.misc import InteractionMode
from graphs.plot_settings import PlotSettingsWindow
from graphs.plot_styles import PlotStylesWindow
from graphs.preferences import PreferencesWindow
from graphs.transform_data import TransformWindow


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
    dialog = Gtk.FileDialog()
    dialog.open_multiple(self.main_window, None, ui.on_add_data_response, self)


def add_data_advanced_action(_action, _target, self):
    AddAdvancedWindow(self)


def add_equation_action(_action, _target, self):
    AddEquationWindow(self)


def select_all_action(_action, _target, self):
    for item in self.datadict.values():
        item.selected = True
    graphs.refresh(self)
    ui.reload_item_menu(self)
    ui.enable_data_dependent_buttons(self, utilities.get_selected_keys(self))


def select_none_action(_action, _target, self):
    for item in self.datadict.values():
        item.selected = False
    graphs.refresh(self)
    ui.reload_item_menu(self)
    ui.enable_data_dependent_buttons(self, False)


def undo_action(_action, _target, self):
    clipboard.undo(self)


def redo_action(_action, _target, self):
    clipboard.redo(self)


def restore_view_action(_action, _target, self):
    self.canvas.dummy_toolbar.home()


def view_back_action(_action, _target, self):
    self.canvas.dummy_toolbar.back()


def view_forward_action(_action, _target, self):
    self.canvas.dummy_toolbar.forward()


def export_data_action(_action, _target, self):
    dialog = Gtk.FileDialog()
    if len(self.datadict) > 1:
        dialog.select_folder(
            self.main_window, None, ui.on_export_data_response, self, True)
    elif len(self.datadict) == 1:
        filename = f"{list(self.datadict.values())[0].name}.txt"
        dialog.set_initial_name(filename)
        dialog.set_filters(
            utilities.create_file_filters([("Text Files", "txt")]))
        dialog.save(
            self.main_window, None, ui.on_export_data_response, self, False)


def export_figure_action(_action, _target, self):
    ExportFigureWindow(self)


def plot_styles_action(_action, _target, self):
    PlotStylesWindow(self)


def save_project_action(_action, _target, self):
    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters([("Graphs Project File", "graphs")]))
    dialog.set_initial_name("project.graphs")
    dialog.save(self.main_window, None, ui.on_save_project_response, self)


def open_project_action(_action, _target, self):
    if len(self.datadict) > 0:
        heading = "Discard Data?"
        body = "Opening a project will discard all open data."
        dialog = Adw.MessageDialog.new(self.main_window,
                                       heading,
                                       body)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("discard", "Discard")
        dialog.set_close_response("cancel")
        dialog.set_default_response("discard")
        dialog.set_response_appearance("discard",
                                       Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", ui.on_confirm_discard_response, self)
        dialog.present()
        return
    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters([("Graphs Project File", "graphs")]))
    dialog.open(self.main_window, None, ui.on_open_project_response, self)


def delete_selected_action(_action, _target, self):
    for key in utilities.get_selected_keys(self):
        graphs.delete_item(self, key, True)


def translate_x_action(_action, _target, self):
    win = self.main_window
    try:
        offset = float(win.translate_x_entry.get_text())
    except ValueError as exception:
        exception_type = exception.__class__.__name__
        message = f"{exception_type}: Unable to do translation, \
make sure to enter a valid number"
        win.add_toast(message)
        logging.exception(message)
        offset = 0
    operations.perform_operation(self, operations.translate_x, offset)


def translate_y_action(_action, _target, self):
    win = self.main_window
    try:
        offset = float(win.translate_y_entry.get_text())
    except ValueError as exception:
        exception_type = exception.__class__.__name__
        message = f"{exception_type}: Unable to do translation, \
make sure to enter a valid number"
        win.add_toast(message)
        logging.exception(message)
        offset = 0
    operations.perform_operation(self, operations.translate_y, offset)


def multiply_x_action(_action, _target, self):
    win = self.main_window
    try:
        multiplier = float(win.multiply_x_entry.get_text())
    except ValueError as exception:
        exception_type = exception.__class__.__name__
        message = f"{exception_type}: Unable to do multiplication, \
make sure to enter a valid number"
        win.add_toast(message)
        logging.exception(message)
        multiplier = 1
    operations.perform_operation(self, operations.multiply_x, multiplier)


def multiply_y_action(_action, _target, self):
    win = self.main_window
    try:
        multiplier = float(win.multiply_y_entry.get_text())
    except ValueError as exception:
        exception_type = exception.__class__.__name__
        message = f"{exception_type}: Unable to do multiplication, \
make sure to enter a valid number"
        win.add_toast(message)
        logging.exception(message)
        multiplier = 1
    operations.perform_operation(self, operations.multiply_y, multiplier)


def normalize_action(_action, _target, self):
    operations.perform_operation(self, operations.normalize)


def smoothen_action(_action, _target, self):
    operations.perform_operation(self, operations.smoothen)


def center_action(_action, _target, self):
    operations.perform_operation(
        self, operations.center,
        self.preferences.config["action_center_data"])


def shift_vertically_action(_action, _target, self):
    selected_keys = utilities.get_selected_keys(self)
    operations.perform_operation(
        self, operations.shift_vertically,
        self.plot_settings.yscale, self.plot_settings.right_scale,
        selected_keys, self.datadict)


def combine_action(_action, _target, self):
    operations.combine(self)


def cut_selected_action(_action, _target, self):
    if self.interaction_mode == InteractionMode.SELECT:
        operations.perform_operation(self, operations.cut_selected)


def get_derivative_action(_action, _target, self):
    operations.perform_operation(self, operations.get_derivative)


def get_integral_action(_action, _target, self):
    operations.perform_operation(self, operations.get_integral)


def get_fourier_action(_action, _target, self):
    operations.perform_operation(self, operations.get_fourier)


def get_inverse_fourier_action(_action, _target, self):
    operations.perform_operation(self, operations.get_inverse_fourier)


def transform_action(_action, _target, self):
    win = TransformWindow(self)
    win.present()
