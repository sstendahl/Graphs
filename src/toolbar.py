# SPDX-License-Identifier: GPL-3.0-or-later
from . import plotting_tools

def pan(widget, shortcut, self):
    if(self.main_window.pan_button.get_active()):
        plotting_tools.set_mode(self, "none")
    else:
        plotting_tools.set_mode(self, "pan")

def view_back(widget, shortcut, self):
    self.dummy_toolbar._nav_stack.back()
    self.dummy_toolbar._update_view()

def view_forward(widget, shortcut, self):
    self.dummy_toolbar._nav_stack.forward()
    self.dummy_toolbar._update_view()

def zoom(widget, shortcut, self):
    if(self.main_window.zoom_button.get_active()):
        plotting_tools.set_mode(self, "none")
    else:
        plotting_tools.set_mode(self, "zoom")


