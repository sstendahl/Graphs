# SPDX-License-Identifier: GPL-3.0-or-later
from . import plotting_tools

def pan(widget, shortcut, self):
    self.dummy_toolbar.pan()
    plotting_tools.set_mode(self, self.dummy_toolbar.mode)

def view_back(widget, shortcut, self):
    self.dummy_toolbar.back()

def view_forward(widget, shortcut, self):
    self.dummy_toolbar.forward()

def zoom(widget, shortcut, self):
    self.dummy_toolbar.zoom()
    plotting_tools.set_mode(self, self.dummy_toolbar.mode)


