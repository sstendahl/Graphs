# SPDX-License-Identifier: GPL-3.0-or-later
import gi
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, Adw, GObject
from matplotlib.backends.backend_gtk4 import NavigationToolbar2GTK4
from . import plotting_tools, plot_settings, utilities
import os
import shutil

@Gtk.Template(resource_path='/se/sjoerd/Graphs/ui/toolbar.ui')
class GraphToolbar(Gtk.Box):
    __gtype_name__ = "GraphToolbar"
    home_button = Gtk.Template.Child()
    backwards_button = Gtk.Template.Child()
    forwards_button = Gtk.Template.Child()
    pan_button = Gtk.Template.Child()
    zoom_button = Gtk.Template.Child()
    yscale_button = Gtk.Template.Child()
    xscale_button = Gtk.Template.Child()
    plot_settings_button = Gtk.Template.Child()

    def __init__(self, canvas, parent):
        super().__init__()
        
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


