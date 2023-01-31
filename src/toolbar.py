# SPDX-License-Identifier: GPL-3.0-or-later

def pan(widget, shortcut, self):
    self.dummy_toolbar.pan()
    button = self.main_window.pan_button
    button.set_active(not button.get_active())

def view_back(widget, shortcut, self):
    self.dummy_toolbar.back()

def view_forward(widget, shortcut, self):
    self.dummy_toolbar.forward()

def zoom(widget, shortcut, self):
    self.dummy_toolbar.zoom()
    button = self.main_window.zoom_button
    button.set_active(not button.get_active())


