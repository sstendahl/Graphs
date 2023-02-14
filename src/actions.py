# SPDX-License-Identifier: GPL-3.0-or-later
from . import ui, preferences, add_data_advanced, graphs
from .misc import InteractionMode

def quit_action(action, target, self):
    self.quit()

def about_action(action, target, self):
    ui.show_about_window(self)

def preferences_action(action, target, self):
    preferences.open_preferences_window(self)

def plot_settings_action(action, target, self):
    plot_settings.open_plot_settings(self)

def add_data_action(action, target, self):
    ui.open_file_dialog(self, False)

def add_data_advanced_action(action, target, self):
    add_data_advanced.open_add_data_advanced_window(self)

def add_equation_action(action, target, self):
    add_equation.open_add_equation_window(self)

def select_all_action(action, target, self):
    graphs.select_all(self)

def select_none_action(action, target, self):
    graphs.select_none(self)

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
