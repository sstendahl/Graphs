# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
from gi.repository import Adw, Gtk

from graphs import clipboard, graphs, operations, plotting_tools, ui, utilities
from graphs.add_data_advanced import AddAdvancedWindow
from graphs.add_equation import AddEquationWindow
from graphs.plot_settings import PlotSettingsWindow
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
    chooser = self.build("dialogs", "open_files")
    chooser.connect("response", ui.on_open_response, self, False)
    chooser.show()


def add_data_advanced_action(_action, _target, self):
    AddAdvancedWindow(self)


def add_equation_action(_action, _target, self):
    AddEquationWindow(self)


def select_all_action(_action, _target, self):
    for _key, item in self.item_rows.items():
        item.check_button.set_active(True)
    plotting_tools.refresh_plot(self)
    ui.enable_data_dependent_buttons(self, utilities.get_selected_keys(self))


def select_none_action(_action, _target, self):
    for _key, item in self.item_rows.items():
        item.check_button.set_active(False)
    plotting_tools.refresh_plot(self)
    ui.enable_data_dependent_buttons(self, False)


def undo_action(_action, _target, self):
    clipboard.undo(self)


def redo_action(_action, _target, self):
    clipboard.redo(self)


def restore_view_action(_action, _target, self):
    plotting_tools.set_canvas_limits_axis(self)
    self.canvas.draw()


def view_back_action(_action, _target, self):
    self.canvas.dummy_toolbar._nav_stack.back()
    self.canvas.dummy_toolbar._update_view()


def view_forward_action(_action, _target, self):
    self.canvas.dummy_toolbar._nav_stack.forward()
    self.canvas.dummy_toolbar._update_view()


def export_data_action(_action, _target, self):
    chooser = self.build("dialogs", "export_data")
    chooser.set_transient_for(self.main_window)
    if len(self.datadict) > 1:
        chooser.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
    elif len(self.datadict) == 1:
        filename = list(self.datadict.values())[0].filename
        chooser.set_current_name(f"{filename}.txt")
    else:
        chooser.destroy
        return
    chooser.connect("response", ui.on_save_response, self, False)
    chooser.show()


def export_figure_action(_action, _target, self):
    ui.export_figure(self)


def save_project_action(_action, _target, self):
    chooser = self.build("dialogs", "save_project")
    chooser.set_transient_for(self.main_window)
    chooser.connect("response", ui.on_save_response, self, True)
    chooser.show()


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
    chooser = self.build("dialogs", "open_project")
    chooser.set_transient_for(self.main_window)
    chooser.connect("response", ui.on_open_response, self, True)
    chooser.show()


def delete_selected_action(_action, _target, self):
    for key in utilities.get_selected_keys(self):
        graphs.delete(self, key, True)


def translate_x_action(_action, _target, self):
    operations.operation(self, operations.translate_x)


def translate_y_action(_action, _target, self):
    operations.operation(self, operations.translate_y)


def multiply_x_action(_action, _target, self):
    operations.operation(self, operations.multiply_x)


def multiply_y_action(_action, _target, self):
    operations.operation(self, operations.multiply_y)


def normalize_action(_action, _target, self):
    operations.operation(self, operations.normalize)


def smoothen_action(_action, _target, self):
    operations.operation(self, operations.smoothen)


def center_action(_action, _target, self):
    operations.operation(self, operations.center)


def shift_vertically_action(_action, _target, self):
    operations.operation(self, operations.shift_vertically)


def combine_action(_action, _target, self):
    operations.operation(self, operations.combine)


def cut_selected_action(_action, _target, self):
    operations.operation(self, operations.cut_selected)


def get_derivative_action(_action, _target, self):
    operations.operation(self, operations.get_derivative)


def get_integral_action(_action, _target, self):
    operations.operation(self, operations.get_integral)


def get_fourier_action(_action, _target, self):
    operations.operation(self, operations.get_fourier)


def get_inverse_fourier_action(_action, _target, self):
    operations.operation(self, operations.get_inverse_fourier)


def transform_action(_action, _target, self):
    win = TransformWindow(self)
    win.present()
