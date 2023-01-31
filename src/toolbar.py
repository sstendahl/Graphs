# SPDX-License-Identifier: GPL-3.0-or-later
import gi
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, Adw, GObject
import os
import shutil

def export_data(widget, shortcut, self):
    self.dummy_toolbar.save_figure()

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


