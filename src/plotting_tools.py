from gi.repository import Gtk, Adw
import copy
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.backends.backend_gtk4agg import (
    FigureCanvasGTK4Agg as FigureCanvas)
from matplotlib.backends.backend_gtk4 import (
    NavigationToolbar2GTK4 as NavigationToolbar)
from . import datman
from matplotlib.widgets import SpanSelector

def define_highlight(self, span=None):
    self.highlight = SpanSelector(
        self.canvas.figure.axes[0],
        on_select,
        "horizontal",
        useblit=True,
        props=dict(alpha=0.3, facecolor = "tab:blue", linewidth = 0),
        handle_props=dict(linewidth=0),
        interactive=True,
        drag_from_anywhere=True)
    if span is not None:
        self.highlight.extents = span
    self.highlight.set_visible(True)
    self.highlight.set_active(True)

def on_select(self, xmin):
    pass

def toggle_highlight(shortcut, _, self):
    win = self.props.active_window
    button = win.select_data_button
    if self.highlight == None:
        define_highlight(self)
    if button.get_active():
        button.set_active(False)
        self.highlight.set_visible(False)
        self.highlight.set_active(False)
    else:
        button.set_active(True)
        self.highlight.set_visible(True)
        self.highlight.set_active(True)
    self.canvas.draw()


def plot_figure(self, canvas, X, Y, filename="", xlim=None, linewidth = 2, title="", scale="log",marker=None, linestyle="solid",
                     revert = False, color = None):
    fig = canvas.ax
    linewidth = linewidth
    if color is not None:
        line = fig.plot(X, Y, linewidth = linewidth ,label=filename, linestyle=linestyle, marker=marker, color = color)
    else:
        line = fig.plot(X, Y, linewidth = linewidth ,label=filename, linestyle=linestyle, marker=marker)
    fig.legend()
    return line

def set_canvas_limits(self, canvas, limits = {"xmin":None, "xmax":None, "ymin":None, "ymax":None}):
    graph_limits = find_limits(self)
    for key, item in limits.items():
        if item is not None:
            graph_limits[key] = item

    span = (graph_limits["xmax"] - graph_limits["xmin"])
    if self.canvas.ax.get_xscale() == "linear":
        graph_limits["xmin"] -= 0.015*span
        graph_limits["xmax"] += 0.015*span
    if self.canvas.ax.get_yscale() == "linear":
        graph_limits["ymin"] *=  0.000
        graph_limits["ymax"] *=  1.05
    else:
        graph_limits["ymin"] *= 0.5
        graph_limits["ymax"] *= 2
    canvas.ax.set_xlim(graph_limits["xmin"], graph_limits["xmax"])
    canvas.ax.set_ylim(graph_limits["ymin"], graph_limits["ymax"])

def find_limits(self):
    xmin_all = None
    xmax_all = None
    ymin_all = None
    ymax_all = None
    for key, item in self.datadict.items():
        if item is not None and len(item.xdata) > 0:
            nonzero_ydata = list(filter(lambda x: (x != 0), item.ydata))
            xmin_item = min(item.xdata)
            xmax_item = max(item.xdata)
            ymin_item = min(nonzero_ydata)
            ymax_item = max(item.ydata)

            if xmin_all == None:
                xmin_all = xmin_item
            if xmax_all == None:
                xmax_all = xmax_item
            if ymin_all == None:
                ymin_all = ymin_item
            if ymax_all == None:
                ymax_all = ymax_item

            if xmin_item < xmin_all:
                xmin_all = xmin_item
            if xmax_item > xmax_all:
                xmax_all = xmax_item
            if (ymin_item < ymin_all):
                ymin_all = ymin_item
            if ymax_item > ymax_all:
                ymax_all = ymax_item
    return {"xmin":xmin_all, "xmax":xmax_all, "ymin":ymin_all, "ymax":ymax_all}


def reload_plot(self, from_dictionary = True):
    datman.clear_layout(self)
    datman.load_empty(self)
    datman.open_selection(self, None, from_dictionary)


def refresh_plot(self, from_dictionary = True, set_limits = True):
    for line in self.canvas.ax.lines:
        line.remove()
    datman.open_selection(self, None, from_dictionary)
    if set_limits and len(self.datadict) > 0:
        set_canvas_limits(self, self.canvas)
    self.canvas.draw()

class PlotWidget(FigureCanvas):
    def __init__(self, parent=None, xlabel="", ylabel="", yscale = "log", title="", scale="linear", style = "seaborn-whitegrid"):
        self.figure = Figure()
        self.figure.set_tight_layout(True)
        self.canvas = FigureCanvas(self.figure)
        self.set_style()
        self.ax = self.figure.add_subplot(111)
        self.set_ax_properties(title, xlabel, ylabel, yscale)
        super(PlotWidget, self).__init__(self.figure)

    def set_ax_properties(self, title = "", xlabel = "", ylabel = "", yscale = "log"):
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        self.ax.set_yscale(yscale)

    def set_style(self):
        plt.rcParams.update(plt.rcParamsDefault)
        if Adw.StyleManager.get_default().get_dark():
            self.figure.patch.set_facecolor('#242424')
            params = {"ytick.color" : "w",
            "xtick.color" : "w",
            "axes.labelcolor" : "w"}
            plt.style.use("dark_background")
        else:
            self.figure.patch.set_facecolor('#FAFAFA')
            params = {"ytick.color" : "black",
            "xtick.color" : "black",
            "axes.labelcolor" : "black"}
            plt.style.use("seaborn-whitegrid")
        plt.rcParams.update(params)

def get_next_color(self):
    color_list = self.color_cycle
    used_colors = []
    item_rows = copy.copy(self.item_rows)
    color_length = len(color_list)
    if len(item_rows) >= color_length:
        item_rows_list = list(item_rows.items())
        item_rows_list = item_rows_list[-color_length+1:]
        item_rows = dict(item_rows_list)
    for key, item in item_rows.items():
        used_colors.append(item.color_picker.color)
    for color in color_list:
        if color not in used_colors:
            return color

