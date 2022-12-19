from gi.repository import Gtk, Adw, GObject, Gio
from . import item_operations, plotting_tools, datman, utilities
from .data import Data
import copy
import os
from matplotlib.lines import Line2D

def open_pip_mode(widget, _, self):
    win = PIPWindow(self)
    win.present()


@Gtk.Template(resource_path="/se/sjoerd/DatMan/pip_mode.ui")
class PIPWindow(Adw.Window):
    __gtype_name__ = "PIPWindow"
    drawing_layout = Gtk.Template.Child()
    def __init__(self, parent):
        super().__init__()
        self.parent = parent


        canvas = parent.canvas
        xlabel = parent.preferences.config["plot_X_label"]
        ylabel = parent.preferences.config["plot_Y_label"]
        canvas = plotting_tools.PlotWidget(parent = parent)
        canvas.ax.set_title(parent.preferences.config["plot_title"])
        canvas.ax.set_xlabel(xlabel, fontweight = parent.preferences.config["plot_font_weight"])
        canvas.ax.set_ylabel(ylabel, fontweight = parent.preferences.config["plot_font_weight"])
        datman.create_layout(parent, canvas, self.drawing_layout, window_type = "pip")
        plotting_tools.refresh_plot(parent, canvas=canvas)
