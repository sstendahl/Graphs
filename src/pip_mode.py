# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gtk, Adw, GObject, Gio
from . import item_operations, plotting_tools, graphs, utilities
from .data import Data
import copy
import os
from matplotlib.lines import Line2D

def open_pip_mode(widget, _, self):
    win = PIPWindow(self)
    win.present()

@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/pip_mode.ui")
class PIPWindow(Adw.Window):
    __gtype_name__ = "PIPWindow"
    drawing_layout = Gtk.Template.Child()
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        canvas = parent.canvas
        xlabel = parent.plot_settings.xlabel
        ylabel = parent.plot_settings.ylabel
        canvas = plotting_tools.PlotWidget(parent = parent)
        canvas.set_ax_properties(parent)
        canvas.ax.set_title(parent.plot_settings.title)
        canvas.ax.set_xlabel(xlabel, fontweight = parent.plot_settings.font_weight)
        canvas.ax.set_ylabel(ylabel, fontweight = parent.plot_settings.font_weight)
        graphs.create_layout(parent, canvas, self.drawing_layout)
        plotting_tools.refresh_plot(parent, canvas=canvas)
