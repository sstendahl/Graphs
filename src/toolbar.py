from gi.repository import Adw
from matplotlib.backends.backend_gtk4 import (
    NavigationToolbar2GTK4 as NavigationToolbar)
from . import plotting_tools, plot_settings, pip_mode, utilities
import os
import shutil


class GraphToolbar(NavigationToolbar):

    def __init__(self, canvas, parent):
        self.parent = parent
        path = os.path.join(os.getenv("XDG_DATA_DIRS"))
        path = path.split(":")[0] + "/datman/datman"

        if Adw.StyleManager.get_default().get_dark():
            backwards_button = f"{path}/backwards-dark"
            forwards_button = f"{path}/forwards-dark"
            home_button = f"{path}/home-dark"
            save_button = f"{path}/save-dark"
            zoom_button = f"{path}/zoom-dark"
            move_button = f"{path}/move-dark"
            xscale_button = f"{path}/change-xscale-dark"
            yscale_button = f"{path}/change-yscale-dark"
            plot_settings_button = f"{path}/plot-settings-dark"
            PIP_button = f"{path}/pip-dark"
        else:
            backwards_button = f"{path}/backwards"
            forwards_button = f"{path}/forwards"
            home_button = f"{path}/home"
            zoom_button = f"{path}/zoom"
            save_button = f"{path}/save"
            move_button = f"{path}/move"
            xscale_button = f"{path}/change-xscale"
            yscale_button = f"{path}/change-yscale"
            plot_settings_button = f"{path}/plot-settings"
            PIP_button = f"{path}/pip"


        self.toolitems = (
            ('Home', 'Restore original view', home_button, 'set_canvas_limits'),
            ('Back', 'Previous view', backwards_button, 'back'),
            ('Forward', 'Next view', forwards_button, 'forward'),
            (None, None, None, None),
            ('Pan', 'Left button to pan, right button to zoom. Hold control to to keep aspect ratio fixed', move_button, 'pan'),
            ('Zoom', 'Zoom to rectangle', zoom_button, 'zoom'),
            ("ChangeYScale", "Change Y-scale", yscale_button, "change_yscale"),
            ("ChangeXScale", "Change X-scale", xscale_button, "change_xscale"),
            ("Settings", "Plot Settings", plot_settings_button, "load_plot_settings"),
            (None, None, None, None),
            ('PIP', 'Open in New Window', PIP_button, 'open_pip_mode'),
            ('Save', 'Save figure', save_button, 'save_figure'),
        )
        super().__init__(canvas, parent)
        
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
            current_scale = self.canvas.ax.get_yscale()
            if current_scale == "linear":
                self.canvas.ax.set_yscale('log')
                self.canvas.set_ticks(self.parent)
                self.parent.plot_settings.yscale = "log"
            elif current_scale == "log":
                self.canvas.ax.set_yscale('linear')
                self.canvas.set_ticks(self.parent)
                self.parent.plot_settings.yscale = "linear"
        if right:
            current_scale = self.canvas.right_axis.get_yscale()
            if current_scale == "linear":
                self.canvas.top_right_axis.set_yscale('log')
                self.canvas.right_axis.set_yscale('log')
                self.canvas.set_ticks(self.parent)
                self.parent.plot_settings.right_scale = "log"
            elif current_scale == "log":
                self.canvas.top_right_axis.set_yscale('linear')
                self.canvas.right_axis.set_yscale('linear')
                self.canvas.set_ticks(self.parent)
                self.parent.plot_settings.right_scale = "linear"
                
        plotting_tools.set_canvas_limits_axis(self.parent, self.canvas)
        self.canvas.draw()

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
            current_scale = self.canvas.top_left_axis.get_xscale()
            if current_scale == "linear":
                self.canvas.top_left_axis.set_xscale('log')
                self.canvas.top_right_axis.set_xscale('log')
                self.canvas.set_ticks(self.parent)
                self.parent.plot_settings.top_scale = "log"
            elif current_scale == "log":
                self.canvas.top_left_axis.set_xscale('linear')
                self.canvas.top_right_axis.set_xscale('linear')
                self.parent.plot_settings.top_scale = "linear"
                self.canvas.set_ticks(self.parent)
        if bottom:
            current_scale = self.canvas.ax.get_xscale()
            if current_scale == "linear":
                self.canvas.ax.set_xscale('log')
                self.canvas.right_axis.set_xscale('log')
                self.canvas.set_ticks(self.parent)
                self.parent.plot_settings.xscale = "log"
            elif current_scale == "log":
                self.canvas.ax.set_xscale('linear')
                self.canvas.right_axis.set_xscale('linear')
                self.parent.plot_settings.xscale = "linear"
                self.canvas.set_ticks(self.parent)

        plotting_tools.set_canvas_limits_axis(self.parent, self.parent.canvas)
        self.canvas.draw()   
