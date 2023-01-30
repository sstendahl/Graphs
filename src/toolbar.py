# SPDX-License-Identifier: GPL-3.0-or-later
import gi
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, Adw, GObject
from matplotlib.backends.backend_gtk4 import NavigationToolbar2GTK4
from . import plotting_tools, plot_settings, pip_mode, utilities
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
    pip_button = Gtk.Template.Child()
    save_button = Gtk.Template.Child()

    def __init__(self, canvas, parent):
        super().__init__()
        self.parent = parent
        win = parent.main_window

        self.toolbar = NavigationToolbar2GTK4(canvas)

        self.home_button.connect("clicked", self.set_canvas_limits)
        self.backwards_button.connect("clicked", self.back)
        self.forwards_button.connect("clicked", self.forward)
        self.pan_button.connect("clicked", self.pan)
        self.zoom_button.connect("clicked", self.zoom)
        self.yscale_button.connect("clicked", self.change_yscale)
        self.xscale_button.connect("clicked", self.change_xscale)
        self.plot_settings_button.connect("clicked", self.load_plot_settings)
        self.pip_button.connect("clicked", self.open_pip_mode)
        self.save_button.connect("clicked", self.save_figure)

    def pan(self, button):
        self.toolbar.pan()

    def back(self, button):
        self.toolbar.back()

    def forward(self, button):
        self.toolbar.forward()

    def zoom(self, button):
        self.toolbar.zoom()

    def save_figure(self, button):
        self.toolbar.save_figure()
        
    def set_canvas_limits(self, button):
        plotting_tools.set_canvas_limits_axis(self.parent, self.parent.canvas)
        self.parent.canvas.draw()

    def load_plot_settings(self, button):
        try:
            plot_settings.open_plot_settings(button, _, self.parent)
        except AttributeError:
            win = self.parent.props.active_window
            win.toast_overlay.add_toast(Adw.Toast(title=f"Unable to open plot settings, make sure to load at least one dataset"))

    def open_pip_mode(self, button):
        pip_mode.open_pip_mode(button, _, self.parent)

    def change_yscale(self, button):
        selected_keys = utilities.get_selected_keys(self.parent)
        left = False
        right = False
        for key in selected_keys:
            if self.parent.datadict[key].plot_Y_position == "left":
                left = True
            if self.parent.datadict[key].plot_Y_position == "right":
                right = True
        
        if left:
            current_scale = self.parent.canvas.ax.get_yscale()
            if current_scale == "linear":
                self.parent.canvas.ax.set_yscale('log')
                self.parent.canvas.set_ticks(self.parent)
                self.parent.plot_settings.yscale = "log"
            elif current_scale == "log":
                self.parent.canvas.ax.set_yscale('linear')
                self.parent.canvas.set_ticks(self.parent)
                self.parent.plot_settings.yscale = "linear"
        if right:
            current_scale = self.parent.canvas.right_axis.get_yscale()
            if current_scale == "linear":
                self.parent.canvas.top_right_axis.set_yscale('log')
                self.parent.canvas.right_axis.set_yscale('log')
                self.parent.canvas.set_ticks(self.parent)
                self.parent.plot_settings.right_scale = "log"
            elif current_scale == "log":
                self.parent.canvas.top_right_axis.set_yscale('linear')
                self.parent.canvas.right_axis.set_yscale('linear')
                self.parent.canvas.set_ticks(self.parent)
                self.parent.plot_settings.right_scale = "linear"
                
        plotting_tools.set_canvas_limits_axis(self.parent, self.parent.canvas)
        self.parent.canvas.draw()

    def change_xscale(self, button):
        selected_keys = utilities.get_selected_keys(self.parent)
        top = False
        bottom = False
        for key in selected_keys:
            if self.parent.datadict[key].plot_X_position == "top":
                top = True
            if self.parent.datadict[key].plot_X_position == "bottom":
                bottom = True
        
        if top:
            current_scale = self.parent.canvas.top_left_axis.get_xscale()
            if current_scale == "linear":
                self.parent.canvas.top_left_axis.set_xscale('log')
                self.parent.canvas.top_right_axis.set_xscale('log')
                self.parent.canvas.set_ticks(self.parent)
                self.parent.plot_settings.top_scale = "log"
            elif current_scale == "log":
                self.parent.canvas.top_left_axis.set_xscale('linear')
                self.parent.canvas.top_right_axis.set_xscale('linear')
                self.parent.parent.plot_settings.top_scale = "linear"
                self.canvas.set_ticks(self.parent)
        if bottom:
            current_scale = self.parent.canvas.ax.get_xscale()
            if current_scale == "linear":
                self.parent.canvas.ax.set_xscale('log')
                self.parent.canvas.right_axis.set_xscale('log')
                self.parent.canvas.set_ticks(self.parent)
                self.parent.plot_settings.xscale = "log"
            elif current_scale == "log":
                self.parent.canvas.ax.set_xscale('linear')
                self.parent.canvas.right_axis.set_xscale('linear')
                self.parent.parent.plot_settings.xscale = "linear"
                self.canvas.set_ticks(self.parent)

        plotting_tools.set_canvas_limits_axis(self.parent, self.parent.canvas)
        self.parent.canvas.draw()   
