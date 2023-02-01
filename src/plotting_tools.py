# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gtk, Adw, Gio, GLib, Gdk, GdkPixbuf
import copy
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.backends.backend_gtk4agg import (
    FigureCanvasGTK4Agg as FigureCanvas)
from matplotlib.backend_bases import _Mode
from . import graphs, utilities, rename_label, toolbar
from matplotlib.widgets import SpanSelector
from cycler import cycler
import matplotlib.font_manager
import time 
import os

def define_highlight(self, span=None):
    """
    Create a span selector object, to highlight part of the graph.
    If a span already exists, make it visible instead
    """
    #This lamdba function is not pretty, but it doesn't accept a "Pass"
    self.highlight = SpanSelector(
        self.canvas.top_right_axis,
        lambda x, y: x,
        "horizontal",
        useblit=True,
        props=dict(alpha=0.3, facecolor = "tab:blue", linewidth = 0),
        handle_props=dict(linewidth=0),
        interactive=True,
        drag_from_anywhere=True)
    if span is not None:
        self.highlight.extents = span

def select(shortcut, _, self):
    """
    Toggle the SpanSelector.
    """
    if self.main_window.select_data_button.get_active():
        set_mode(self, "none")
    else:
        set_mode(self, "select/cut")


def plot_figure(self, canvas, X, Y, filename="", xlim=None, linewidth = 2, title="", scale="log",marker=None, linestyle="solid",
                     revert = False, color = None, marker_size = 10, y_axis = "left", x_axis = "bottom"):
    """
    Plot the figure on the graph
    Necessary input arguments are self, the canvas to plot the figure on and the
    X and Y data
    """
    if y_axis == "left":
        if x_axis == "bottom":
            canvas.ax.plot(X, Y, linewidth = linewidth ,label=filename, linestyle=linestyle, marker=marker, color = color, markersize=marker_size)
        elif x_axis == "top":
            canvas.top_left_axis.plot(X, Y, linewidth = linewidth ,label=filename, linestyle=linestyle, marker=marker, color = color, markersize=marker_size)
    elif y_axis == "right":
        if x_axis == "bottom":
            canvas.right_axis.plot(X, Y, linewidth = linewidth ,label=filename, linestyle=linestyle, marker=marker, color = color, markersize=marker_size)
        elif x_axis == "top":
            canvas.top_right_axis.plot(X, Y, linewidth = linewidth ,label=filename, linestyle=linestyle, marker=marker, color = color, markersize=marker_size)
    set_legend(self, canvas)

def set_legend(self, canvas):
    """
    Set the legend of the graph
    """
    if self.plot_settings.legend:
        canvas.legends = []
        lines, labels = canvas.ax.get_legend_handles_labels()
        lines2, labels2 = canvas.right_axis.get_legend_handles_labels()
        lines3, labels3 = canvas.top_left_axis.get_legend_handles_labels()
        lines4, labels4 = canvas.top_right_axis.get_legend_handles_labels()
        canvas.top_right_axis.legend(lines + lines2 + lines3 + lines4, labels + labels2 + labels3 + labels4, loc=0, frameon=True)

def set_canvas_limits_axis(self, canvas, limits = {"xmin":None, "xmax":None, "ymin":None, "ymax":None}):
    """
    Set the canvas limits for each axis that is present
    """
    left_datadict = dict()
    right_datadict = dict()
    top_datadict = dict()
    bottom_datadict = dict()
    graph_limits = limits
    for axis in [canvas.ax, canvas.right_axis, canvas.top_left_axis, canvas.top_right_axis]:
        graph_limits_new = find_limits(self, axis, canvas, self.datadict)
        if graph_limits_new["xmin"] is not None:
            graph_limits = graph_limits_new
            set_canvas_limits(self, graph_limits, axis)
            
def set_canvas_limits(self, graph_limits, axis, limits = {"xmin":None, "xmax":None, "ymin":None, "ymax":None}):
    """
    Set an calculate the canvas limits for a given axis.
    """

    #Update graph limits with limits that were given as argument
    for key, item in limits.items():
        if item is not None:
            graph_limits[key] = item

    x_span = (graph_limits["xmax"] - graph_limits["xmin"])
    y_span = (graph_limits["ymax"] - graph_limits["ymin"]) 
    if axis.get_xscale() == "linear":
        graph_limits["xmin"] -= 0.015*x_span
        graph_limits["xmax"] += 0.015*x_span
    if axis.get_yscale() == "linear":
        if y_span != 0:
            if graph_limits["ymin"] > 0:
                graph_limits["ymin"] *= 0.95
            else:
                graph_limits["ymin"] *= 1.05
            graph_limits["ymax"] *= 1.05        
        else:
            graph_limits["ymax"] +=  abs(graph_limits["ymax"]*0.05)            
            graph_limits["ymin"] -=  abs(graph_limits["ymin"]*0.05)
    else:
        graph_limits["ymin"] *= 0.5
        graph_limits["ymax"] *= 2
    try:
        axis.set_xlim(graph_limits["xmin"], graph_limits["xmax"])
        axis.set_ylim(graph_limits["ymin"], graph_limits["ymax"])
    except ValueError:
        print("Could not set limits, one of the values was probably infinite")
        
def find_limits(self, axis, canvas, datadict):
    """
    Find the limits that are to be used for the axes.
    """
    xmin_all = None
    xmax_all = None
    ymin_all = None
    ymax_all = None

    #Check which xaxis and yaxis are being used based on the axis given
    if axis == canvas.ax:
        xaxis = "bottom"
        yaxis = "left"
    elif axis == canvas.right_axis:
        xaxis = "bottom"
        yaxis = "right"
    elif axis == canvas.top_left_axis:
        xaxis = "top"
        yaxis = "left"
    elif axis == canvas.top_right_axis:
        xaxis = "top"
        yaxis = "right"    

    for key, item in datadict.items():
        #Check the limits of each item, as long as it exists and it has the same axes as the one we're adjusting right now
        if item is not None and len(item.xdata) > 0 and item.plot_Y_position == yaxis and item.plot_X_position == xaxis:
            #Nonzero ydata is needed for logs
            nonzero_ydata = list(filter(lambda x: (x != 0), item.ydata))
            xmin_item = min(item.xdata)
            xmax_item = max(item.xdata)
            if len(nonzero_ydata) > 0:
                ymin_item = min(nonzero_ydata)
            else:
                ymin_item = min(item.ydata)
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
    """
    Completely reload the plot of the graph
    """
    win = self.props.active_window
    graphs.load_empty(self)
    if len(self.datadict) > 0:
        hide_unused_axes(self, self.canvas)
        graphs.open_selection(self, None, from_dictionary)
        if (not self.highlight == None):
            self.highlight.set_visible(False)
            self.highlight.set_active(False)
            self.highlight = None
        set_mode(self, self._mode)
        set_canvas_limits_axis(self, self.canvas)
    self.canvas.grab_focus()


def refresh_plot(self, canvas = None, from_dictionary = True, set_limits = True):
    """
    Refresh the graph without completely reloading it.
    """
    if canvas == None:
        canvas = self.canvas
    for line in canvas.ax.lines:
        line.remove()
    for line in canvas.right_axis.lines:
        line.remove()
    for line in canvas.top_left_axis.lines:
        line.remove()
    for line in canvas.top_right_axis.lines:
        line.remove()
    if len(self.datadict) > 0:
        hide_unused_axes(self, canvas)
    graphs.open_selection(self, None, from_dictionary, canvas = canvas)
    if set_limits and len(self.datadict) > 0:
        set_canvas_limits_axis(self, canvas)
    self.canvas.draw()

def hide_unused_axes(self, canvas):
    """
    Hide axes that are not in use, to avoid unnecessary ticks in the plots.
    """
    #Double check the code here, seems to work but this is too messy
    for axis in [canvas.ax, canvas.right_axis, canvas.top_left_axis, canvas.top_right_axis]:
        axis.get_xaxis().set_visible(True)
        axis.get_yaxis().set_visible(True)
    left = False
    right = False
    top = False
    bottom = False
    for key, item in self.datadict.items():
        if item.plot_Y_position == "left":
            left = True
        if item.plot_Y_position == "right":
            right = True
        if item.plot_X_position == "top":
            top = True
        if item.plot_X_position == "bottom":
            bottom = True
    if not left:
        canvas.top_left_axis.get_yaxis().set_visible(False)
        canvas.ax.get_yaxis().set_visible(False)
    if not right:
        canvas.top_right_axis.get_yaxis().set_visible(False)
        canvas.right_axis.get_yaxis().set_visible(False)
    if not top:
        canvas.top_right_axis.get_xaxis().set_visible(False)
        canvas.top_left_axis.get_xaxis().set_visible(False)
    if not bottom:
        canvas.ax.get_xaxis().set_visible(False)
        canvas.right_axis.get_xaxis().set_visible(False)

    canvas.top_right_axis.get_xaxis().set_visible(False)
    canvas.right_axis.get_xaxis().set_visible(False)
    canvas.top_right_axis.get_yaxis().set_visible(False)
    canvas.top_left_axis.get_yaxis().set_visible(False)

def change_yscale(widget, shortcut, self):
    selected_keys = utilities.get_selected_keys(self)
    left = False
    right = False
    for key in selected_keys:
        if self.datadict[key].plot_Y_position == "left":
            left = True
        if self.datadict[key].plot_Y_position == "right":
            right = True

    if left:
        current_scale = self.canvas.ax.get_yscale()
        if current_scale == "linear":
            self.canvas.ax.set_yscale('log')
            self.canvas.set_ticks(self)
            self.plot_settings.yscale = "log"
        elif current_scale == "log":
            self.canvas.ax.set_yscale('linear')
            self.canvas.set_ticks(self)
            self.plot_settings.yscale = "linear"
    if right:
        current_scale = self.canvas.right_axis.get_yscale()
        if current_scale == "linear":
            self.canvas.top_right_axis.set_yscale('log')
            self.canvas.right_axis.set_yscale('log')
            self.canvas.set_ticks(self)
            self.plot_settings.right_scale = "log"
        elif current_scale == "log":
            self.canvas.top_right_axis.set_yscale('linear')
            self.canvas.right_axis.set_yscale('linear')
            self.canvas.set_ticks(self)
            self.plot_settings.right_scale = "linear"

    set_canvas_limits_axis(self, self.canvas)
    self.canvas.draw()

def change_xscale(widget, shortcut, self):
    selected_keys = utilities.get_selected_keys(self)
    top = False
    bottom = False
    for key in selected_keys:
        if self.datadict[key].plot_X_position == "top":
            top = True
        if self.datadict[key].plot_X_position == "bottom":
            bottom = True

    if top:
        current_scale = self.canvas.top_left_axis.get_xscale()
        if current_scale == "linear":
            self.canvas.top_left_axis.set_xscale('log')
            self.canvas.top_right_axis.set_xscale('log')
            self.canvas.set_ticks(self)
            self.plot_settings.top_scale = "log"
        elif current_scale == "log":
            self.canvas.top_left_axis.set_xscale('linear')
            self.canvas.top_right_axis.set_xscale('linear')
            self.plot_settings.top_scale = "linear"
            self.canvas.set_ticks(self)
    if bottom:
        current_scale = self.canvas.ax.get_xscale()
        if current_scale == "linear":
            self.canvas.ax.set_xscale('log')
            self.canvas.right_axis.set_xscale('log')
            self.canvas.set_ticks(self)
            self.plot_settings.xscale = "log"
        elif current_scale == "log":
            self.canvas.ax.set_xscale('linear')
            self.canvas.right_axis.set_xscale('linear')
            self.plot_settings.xscale = "linear"
            self.canvas.set_ticks(self)

    set_canvas_limits_axis(self, self.canvas)
    self.canvas.draw()

def restore_view(widget, shortcut, self):
    set_canvas_limits_axis(self, self.canvas)
    self.canvas.draw()

def get_next_color(self):
    """
    Get the color that is to be used for the next data set
    """
    color_list = self.canvas.color_cycle
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

def load_fonts(self):
    """
    Load system fonts that are installed on the system
    """
    font_list = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    for font in font_list:
        try:
            matplotlib.font_manager.fontManager.addfont(font)
        except:
            print(f"Could not load {font}")
            
def set_mode(self, mode):
    """
    Set the current UI interaction mode (pan, zoom or select/cut)
    """
    win = self.main_window
    pan_button = win.pan_button
    zoom_button = win.zoom_button
    select_button = win.select_data_button
    cut_button = win.cut_data_button
    if self.highlight == None:
        define_highlight(self)
    highlight = self.highlight
    if(mode == "none"):
        self.dummy_toolbar.mode = _Mode.NONE
        pan_button.set_active(False)
        zoom_button.set_active(False)
        select_button.set_active(False)
        cut_button.set_visible(False)
        highlight.set_visible(False)
        highlight.set_active(False)
    elif(mode == "pan"):
        self.dummy_toolbar.mode = _Mode.PAN
        pan_button.set_active(True)
        zoom_button.set_active(False)
        select_button.set_active(False)
        cut_button.set_visible(False)
        highlight.set_visible(False)
        highlight.set_active(False)
    elif(mode == "zoom"):
        self.dummy_toolbar.mode = _Mode.ZOOM
        pan_button.set_active(False)
        zoom_button.set_active(True)
        select_button.set_active(False)
        cut_button.set_visible(False)
        highlight.set_visible(False)
        highlight.set_active(False)
    elif(mode == "select/cut"):
        self.dummy_toolbar.mode = _Mode.NONE
        pan_button.set_active(False)
        zoom_button.set_active(False)
        select_button.set_active(True)
        cut_button.set_visible(True)
        highlight.set_visible(True)
        highlight.set_active(True)
    for axis in self.canvas.figure.get_axes():
            axis.set_navigate_mode(self.dummy_toolbar.mode._navigate_mode)
    self._mode = mode
    self.canvas.draw()

# https://github.com/matplotlib/matplotlib/blob/c23ccdde6f0f8c071b09a88770e24452f2859e99/lib/matplotlib/backends/backend_gtk4.py#L306
def export_data(widget, shortcut, self):
    dialog = Gtk.FileChooserNative(
        title='Save the figure',
        transient_for=self.main_window,
        action=Gtk.FileChooserAction.SAVE,
        modal=True)
    self._save_dialog = dialog  # Must keep a reference.

    ff = Gtk.FileFilter()
    ff.set_name('All files')
    ff.add_pattern('*')
    dialog.add_filter(ff)
    dialog.set_filter(ff)

    formats = []
    default_format = None
    for i, (name, fmts) in enumerate(
            self.canvas.get_supported_filetypes_grouped().items()):
        ff = Gtk.FileFilter()
        ff.set_name(name)
        for fmt in fmts:
            ff.add_pattern(f'*.{fmt}')
        dialog.add_filter(ff)
        formats.append(name)
        if self.canvas.get_default_filetype() in fmts:
            default_format = i
    # Setting the choice doesn't always work, so make sure the default
    # format is first.
    formats = [formats[default_format], *formats[:default_format],
               *formats[default_format+1:]]
    dialog.add_choice('format', 'File format', formats, formats)
    dialog.set_choice('format', formats[default_format])

    dialog.set_current_name(self.canvas.get_default_filename())
    dialog.connect("response", on_save_response, self)
    dialog.show()

# https://github.com/matplotlib/matplotlib/blob/c23ccdde6f0f8c071b09a88770e24452f2859e99/lib/matplotlib/backends/backend_gtk4.py#L344
def on_save_response(dialog, response, self):
    file = dialog.get_file()
    fmt = dialog.get_choice('format')
    fmt = self.canvas.get_supported_filetypes_grouped()[fmt][0]
    dialog.destroy()
    self._save_dialog = None
    if response != Gtk.ResponseType.ACCEPT:
        return
    try:
        self.canvas.figure.savefig(file.get_path(), format=fmt)
    except Exception as e:
        self.main_window.toast_overlay.add_toast(Adw.Toast(title=f"Unable to save image"))

class PlotSettings:
    """
    The plot-related settings for the current session. The default values are
    retreived from the config file through preferences.
    """
    def __init__(self, parent):
        self.font_string = parent.preferences.config["plot_font_string"]
        self.xlabel = parent.preferences.config["plot_X_label"]
        self.right_label = parent.preferences.config["plot_right_label"]
        self.top_label = parent.preferences.config["plot_top_label"]
        self.ylabel = parent.preferences.config["plot_Y_label"]
        self.xscale = parent.preferences.config["plot_X_scale"]
        self.yscale = parent.preferences.config["plot_Y_scale"]
        self.right_scale = parent.preferences.config["plot_right_scale"]
        self.top_scale = parent.preferences.config["plot_top_scale"]
        self.title = parent.preferences.config["plot_title"]
        self.font_weight = parent.preferences.config["plot_font_weight"]
        self.font_family = parent.preferences.config["plot_font_family"]
        self.font_size = parent.preferences.config["plot_font_size"]
        self.font_style = parent.preferences.config["plot_font_style"]
        self.tick_direction = parent.preferences.config["plot_tick_direction"]
        self.major_tick_length = parent.preferences.config["plot_major_tick_length"]
        self.minor_tick_length = parent.preferences.config["plot_minor_tick_length"]
        self.major_tick_width = parent.preferences.config["plot_major_tick_width"]
        self.minor_tick_width = parent.preferences.config["plot_minor_tick_width"]
        self.tick_top = parent.preferences.config["plot_tick_top"]
        self.tick_bottom = parent.preferences.config["plot_tick_bottom"]
        self.tick_left = parent.preferences.config["plot_tick_left"]
        self.tick_right = parent.preferences.config["plot_tick_right"]
        self.legend = parent.preferences.config["plot_legend"]
        if Adw.StyleManager.get_default().get_dark(): 
            self.plot_style = parent.preferences.config["plot_style_dark"]
        else:
            self.plot_style = parent.preferences.config["plot_style_light"]

        
class PlotWidget(FigureCanvas):
    """
    Create the widget that contains the graph itself
    """
    def __init__(self, parent=None, xlabel="", ylabel="", yscale = "log", title="", scale="linear", style = "seaborn-whitegrid"):
        self.figure = Figure()
        self.figure.set_tight_layout(True)
        self.canvas = FigureCanvas(self.figure)
        self.one_click_trigger = False
        self.time_first_click  = 0
        self.parent = parent
        self.canvas.mpl_connect('button_release_event', self)
        self.set_style(parent)
        self.ax = self.figure.add_subplot(111)
        self.right_axis = self.ax.twinx()
        self.top_left_axis = self.ax.twiny()
        self.top_right_axis = self.top_left_axis.twinx()

        #Set the coordinates in the bottom-right corner as an empty string
        #These only work for the top-right axis anyway, so is broken in 95% of
        #the cases, and makes the experience very bad for small window sizes.
        #This feature should be implemented differently perhaps.
        self.top_right_axis.format_coord = lambda x, y: ""
        self.set_ax_properties(parent)
        self.set_save_properties(parent)
        self.set_color_cycle(parent)
        super(PlotWidget, self).__init__(self.figure)

    def set_save_properties(self, parent):
        """
        Set the properties that are related to saving the figure. Currently
        limited to savefig, but will include the background colour soon.
        """
        plt.rcParams["savefig.format"] = parent.preferences.config["savefig_filetype"]
        if parent.preferences.config["savefig_transparent"]:
            plt.rcParams["savefig.transparent"] = True

    def set_ax_properties(self, parent):
        """
        Set the properties that are related to the axes.
        """
        self.title = self.ax.set_title(parent.plot_settings.title)
        self.bottom_label = self.ax.set_xlabel(parent.plot_settings.xlabel, fontweight = parent.plot_settings.font_weight)
        self.right_label = self.right_axis.set_ylabel(parent.plot_settings.right_label, fontweight = parent.plot_settings.font_weight)
        self.top_label = self.top_left_axis.set_xlabel(parent.plot_settings.top_label, fontweight = parent.plot_settings.font_weight)
        self.left_label = self.ax.set_ylabel(parent.plot_settings.ylabel, fontweight = parent.plot_settings.font_weight)
        self.ax.set_yscale(parent.plot_settings.yscale)
        self.right_axis.set_yscale(parent.plot_settings.right_scale)
        self.top_left_axis.set_xscale(parent.plot_settings.top_scale)
        self.top_right_axis.set_xscale(parent.plot_settings.top_scale)
        self.ax.set_xscale(parent.plot_settings.xscale)
        self.set_ticks(parent)

    def set_ticks(self, parent):
        """
        Set the ticks that are to be used in the graph.
        """
        for axis in [self.top_right_axis, self.top_left_axis, self.ax, self.right_axis]:
            axis.tick_params(direction=parent.plot_settings.tick_direction, length=parent.plot_settings.major_tick_length, width=parent.plot_settings.major_tick_width, which="major")
            axis.tick_params(direction=parent.plot_settings.tick_direction, length=parent.plot_settings.minor_tick_length, width=parent.plot_settings.minor_tick_width, which="minor")
            axis.tick_params(axis='x',which='minor')
            axis.tick_params(axis='y',which='minor')
            axis.minorticks_on()
            top = False
            bottom = False
            left = False
            right = False
            for key in parent.datadict.keys():
                if parent.datadict[key].plot_X_position == "top":
                    top = True
                if parent.datadict[key].plot_X_position == "bottom":
                    bottom = True
                if parent.datadict[key].plot_Y_position == "left":
                    left = True
                if parent.datadict[key].plot_Y_position == "right":
                    right = True
            if not (top and bottom):
                axis.tick_params(which = "both", bottom=parent.plot_settings.tick_bottom, top=parent.plot_settings.tick_top)
            if not (left and right):
                axis.tick_params(which = "both", left=parent.plot_settings.tick_left, right=parent.plot_settings.tick_right)

    def set_style(self, parent):
        """
        Set the plot style.
        """
        plt.rcParams.update(plt.rcParamsDefault)
        if Adw.StyleManager.get_default().get_dark():
            self.figure.patch.set_facecolor("#242424")
            params = {"ytick.color" : "w",
            "xtick.color" : "w",
            "axes.labelcolor" : "w",
            "font.family": "sans-serif",
            "font.weight": parent.plot_settings.font_weight,
            "font.sans-serif": parent.plot_settings.font_family,
            "font.size": parent.plot_settings.font_size,
            "font.style": parent.plot_settings.font_style,
            "mathtext.default": "regular"
            }
            plt.style.use(parent.plot_settings.plot_style)
        else:
            self.figure.patch.set_facecolor("#fafafa")
            params = {"ytick.color" : "black",
            "xtick.color" : "black",
            "axes.labelcolor" : "black",
            "font.family": "sans-serif",
            "font.weight": parent.plot_settings.font_weight,
            "font.sans-serif": parent.plot_settings.font_family,
            "font.size": parent.plot_settings.font_size,
            "font.style": parent.plot_settings.font_style,
            "mathtext.default": "regular"
            }
            plt.style.use(parent.plot_settings.plot_style)
        plt.rcParams.update(params)

    def set_color_cycle(self, parent):
        """
        Set the color cycle that will be used for the graphs.
        """
        cmap = parent.preferences.config["plot_color_cycle"]
        reverse_dark = parent.preferences.config["plot_invert_color_cycle_dark"]
        if Adw.StyleManager.get_default().get_dark() and reverse_dark:
            cmap += "_r"
        color_cycle = cycler(color=plt.get_cmap(cmap).colors)
        self.color_cycle = color_cycle.by_key()['color']

    def __call__(self, event):
        """
        The function is called when a user clicks on it.
        If two clicks are performed close to each other, it registers as a double
        click, and if these were on a specific item (e.g. the title) it triggers
        a dialog to edit this item.

        Unfortunately the GTK Doubleclick signal doesn't work with matplotlib
        hence this custom function.
        """
        double_click = False
        if self.one_click_trigger == False:
            self.one_click_trigger = True
            self.time_first_click = time.time()
        else:
            double_click_interval = time.time() - self.time_first_click
            if double_click_interval > 0.5:
                self.one_click_trigger = True
                self.time_first_click = time.time()
            else:
                self.one_click_trigger = False
                self.time_first_click = 0 
                double_click = True
                
        if self.title.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.title)
        if self.top_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.top_label)
        if self.bottom_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.bottom_label)
        if self.left_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.left_label)
        if self.right_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.right_label)
