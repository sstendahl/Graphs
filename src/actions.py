# SPDX-License-Identifier: GPL-3.0-or-later
"""Main actions."""
from graphs import graphs, item_operations, plot_settings, plotting_tools, ui, utilities
from graphs.add_data_advanced import AddAdvancedWindow
from graphs.add_equation import AddEquationWindow
from graphs.preferences import PreferencesWindow
from graphs.transform_data import TransformWindow


def quit_action(_action, _target, self):
    self.quit()


def about_action(_action, _target, self):
    ui.show_about_window(self)


def preferences_action(_action, _target, self):
    win = PreferencesWindow(self)
    win.present()


def plot_settings_action(_action, _target, self):
    plot_settings.open_plot_settings(self)


def add_data_action(_action, _target, self):
    ui.open_file_dialog(self, False)


def add_data_advanced_action(_action, _target, self):
    win = AddAdvancedWindow(self)
    win.present()


def add_equation_action(_action, _target, self):
    win = AddEquationWindow(self)
    win.present()


def select_all_action(_action, _target, self):
    for _key, item in self.item_rows.items():
        item.check_button.set_active(True)
    plotting_tools.refresh_plot(self)
    ui.enable_data_dependent_buttons(self, True)


def select_none_action(_action, _target, self):
    for _key, item in self.item_rows.items():
        item.check_button.set_active(False)
    plotting_tools.refresh_plot(self)
    ui.enable_data_dependent_buttons(self, False)


def undo_action(_action, _target, self):
    item_operations.undo(self)


def redo_action(_action, _target, self):
    item_operations.redo(self)


def restore_view_action(_action, _target, self):
    plotting_tools.set_canvas_limits_axis(self, self.canvas)
    self.canvas.draw()


def view_back_action(_action, _target, self):
    self.dummy_toolbar._nav_stack.back()
    self.dummy_toolbar._update_view()


def view_forward_action(_action, _target, self):
    self.dummy_toolbar._nav_stack.forward()
    self.dummy_toolbar._update_view()


def export_data_action(_action, _target, self):
    ui.save_file_dialog(self)


def export_figure_action(_action, _target, self):
    ui.export_figure(self)


def save_project_action(_action, _target, self):
    ui.save_project_dialog(self)


def open_project_action(_action, _target, self):
    ui.open_file_dialog(self, True)


def delete_selected_action(_action, _target, self):
    for key in utilities.get_selected_keys(self):
        graphs.delete(self, key, True)


def translate_x_action(_action, _target, self):
    item_operations.translate_x(self)


def translate_y_action(_action, _target, self):
    item_operations.translate_y(self)


def multiply_x_action(_action, _target, self):
    item_operations.multiply_x(self)


def multiply_y_action(_action, _target, self):
    item_operations.multiply_y(self)


def normalize_action(_action, _target, self):
    item_operations.normalize_data(self)


def smoothen_action(_action, _target, self):
    item_operations.smoothen_data(self)


def center_action(_action, _target, self):
    item_operations.center_data(self)


def shift_vertically_action(_action, _target, self):
    item_operations.shift_vertically(self)


def combine_action(_action, _target, self):
    item_operations.combine_data(self)


def cut_selected_action(_action, _target, self):
    item_operations.cut_data(self)


def get_derivative_action(_action, _target, self):
    item_operations.get_derivative(self)


def get_integral_action(_action, _target, self):
    item_operations.get_integral(self)


def get_fourier_action(_action, _target, self):
    item_operations.get_fourier(self)


def get_inverse_fourier_action(_action, _target, self):
    item_operations.get_inverse_fourier(self)


def transform_action(_action, _target, self):
    win = TransformWindow(self)
    win.present()
