# SPDX-License-Identifier: GPL-3.0-or-later
from . import ui, utilities, plot_settings, graphs, item_operations
from .misc import InteractionMode
from .preferences import PreferencesWindow
from .add_data_advanced import AddAdvancedWindow
from .add_equation import AddEquationWindow
from .transform_data import TransformWindow

def quit_action(action, target, self):
    self.quit()

def about_action(action, target, self):
    ui.show_about_window(self)

def preferences_action(action, target, self):
    win = PreferencesWindow(self)
    win.set_transient_for(self.main_window)
    win.present()

def plot_settings_action(action, target, self):
    plot_settings.open_plot_settings(self)

def add_data_action(action, target, self):
    ui.open_file_dialog(self, False)

def add_data_advanced_action(action, target, self):
    win = AddAdvancedWindow(self)
    win.set_transient_for(self.main_window)
    win.set_modal(True)
    win.present()

def add_equation_action(action, target, self):
    win = AddEquationWindow(self)
    win.set_transient_for(self.main_window)
    win.set_modal(True)
    win.present()

def select_all_action(action, target, self):
    for key, item in self.item_rows.items():
        item.check_button.set_active(True)
    graphs.toggle_data(None, self)

def select_none_action(action, target, self):
    for key, item in self.item_rows.items():
        item.check_button.set_active(False)
    graphs.toggle_data(None, self)

def undo_action(action, target, self):
    item_operations.undo(self)

def redo_action(action, target, self):
    item_operations.redo(self)

def restore_view_action(action, target, self):
    plotting_tools.set_canvas_limits_axis(self, self.canvas)
    self.canvas.draw()

def view_back_action(action, target, self):
    self.dummy_toolbar._nav_stack.back()
    self.dummy_toolbar._update_view()

def view_forward_action(action, target, self):
    self.dummy_toolbar._nav_stack.forward()
    self.dummy_toolbar._update_view()

def export_data_action(action, target, self):
    ui.save_file_dialog(self)

def export_figure_action(action, target, self):
    ui.export_figure(self)

def save_project_action(action, target, self):
    ui.save_project_dialog(self)

def open_project_action(action, target, self):
    ui.open_file_dialog(self, True)

def delete_selected_action(action, target, self):
    for key in utilities.get_selected_keys(self):
        graphs.delete(self, key, True)

def translate_x_action(action, target, self):
    item_operations.translate_x(self)

def translate_y_action(action, target, self):
    item_operations.translate_y(self)

def multiply_x_action(action, target, self):
    item_operations.multiply_x(self)

def multiply_y_action(action, target, self):
    item_operations.multiply_y(self)

def normalize_action(action, target, self):
    item_operations.normalize_data(self)

def smoothen_action(action, target, self):
    item_operations.smoothen_data(self)

def center_action(action, target, self):
    item_operations.center_data(self)

def shift_vertically_action(action, target, self):
    item_operations.shift_vertically(self)

def combine_action(action, target, self):
    item_operations.combine_data(self)

def cut_selected_action(action, target, self):
    item_operations.cut_data(self)

def get_derivative_action(action, target, self):
    item_operations.get_derivative(self)

def get_integral_action(action, target, self):
    item_operations.get_integral(self)

def get_fourier_action(action, target, self):
    item_operations.get_fourier(self)

def get_inverse_fourier_action(action, target, self):
    item_operations.get_inverse_fourier(self)

def transform_action(action, target, self):
    win = TransformWindow(self)
    win.set_transient_for(self.main_window)
    win.set_modal(True)
    win.present()
