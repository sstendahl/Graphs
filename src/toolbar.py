from matplotlib.backends.backend_gtk4 import (
    NavigationToolbar2GTK4 as NavigationToolbar)
from . import plotting_tools
import os
import shutil


class GraphToolbar(NavigationToolbar):

    def __init__(self, canvas, parent):
        self.parent = parent
        path = os.path.join(os.getenv("XDG_DATA_DIRS"))
        path = path.split(":")[0] + "/icons/hicolor/symbolic/apps/se.sjoerd.DatMan"
        test = path

        self.toolitems = (
            ('Home', 'Restore original view', 'home', 'home'),
            ('Back', 'Previous view', "back", 'back'),
            ('Forward', 'Next view', 'forward', 'forward'),
            (None, None, None, None),
            ('Pan', 'Left button pans, right button zooms. Hold control to fix aspect ratio', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
            ("Customize", "Change Y-scale", test, "change_yscale"),
            ("Customize", "Change Y-scale", "forward", "change_xscale"),
            (None, None, None, None),
            ('Save', 'Save figure', 'filesave', 'save_figure'),
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

        
