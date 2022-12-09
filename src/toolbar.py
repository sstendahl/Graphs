from gi.repository import Adw
from matplotlib.backends.backend_gtk4 import (
    NavigationToolbar2GTK4 as NavigationToolbar)
from . import plotting_tools
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
        else:
            backwards_button = f"{path}/backwards"
            forwards_button = f"{path}/forwards"
            home_button = f"{path}/home"
            zoom_button = f"{path}/zoom"
            save_button = f"{path}/save"
            move_button = f"{path}/move"
            xscale_button = f"{path}/change-xscale"
            yscale_button = f"{path}/change-yscale"


        self.toolitems = (
            ('Home', 'Restore original view', home_button, 'home'),
            ('Back', 'Previous view', backwards_button, 'back'),
            ('Forward', 'Next view', forwards_button, 'forward'),
            (None, None, None, None),
            ('Pan', 'Left button to pan, right button to zoom. Hold control to to keep aspect ratio fixed', move_button, 'pan'),
            ('Zoom', 'Zoom to rectangle', zoom_button, 'zoom'),
            ("Customize", "Change Y-scale", yscale_button, "change_yscale"),
            ("Customize", "Change Y-scale", xscale_button, "change_xscale"),
            (None, None, None, None),
            ('Save', 'Save figure', save_button, 'save_figure'),
        )
        super().__init__(canvas, parent)

    def change_yscale(self, button):
        current_scale = self.canvas.ax.get_yscale()
        if current_scale == "linear":
            self.canvas.ax.set_yscale('log')
        elif current_scale == "log":
            self.canvas.ax.set_yscale('linear')
        plotting_tools.set_canvas_limits(self.parent, self.canvas)
        self.canvas.draw()

    def change_xscale(self, button):
        current_scale = self.canvas.ax.get_xscale()
        if current_scale == "linear":
            self.canvas.ax.set_xscale('log')
        elif current_scale == "log":
            self.canvas.ax.set_xscale('linear')
        plotting_tools.set_canvas_limits(self.parent, self.parent.canvas)
        self.canvas.draw()

        
