# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import os
import time
import matplotlib.font_manager
import matplotlib.pyplot as plt

from gi.repository import Gtk, Adw
from matplotlib import colors
from matplotlib.backends.backend_gtk4cairo import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
from cycler import cycler

from . import graphs, utilities, rename_label

def define_highlight(self, span=None):
    """
    Create a span selector object, to highlight part of the graph.
    If a span already exists, make it visible instead
    """
    self.highlight = SpanSelector(
        self.canvas.top_right_axis,
        lambda x, y: on_highlight_define(self),
        "horizontal",
        useblit=True,
        props=dict(facecolor = (120 / 255, 174 / 255, 237 / 255, 0.2), edgecolor = (120 / 255, 174 / 255, 237 / 255, 1), linewidth = 1),
        handle_props=dict(linewidth=0),
        interactive=True,
        drag_from_anywhere=True)
    if span is not None:
        self.highlight.extents = span

def on_highlight_define(self):
    """
    This ensures that the span selector doesn't go out of range
    There are some obscure cases where this otherwise happens, and the selection
    tool becomes unusable.
    """
    xmin = min(self.canvas.top_right_axis.get_xlim())
    xmax = max(self.canvas.top_right_axis.get_xlim())
    extend_min = self.highlight.extents[0]
    extend_max = self.highlight.extents[1]    
    if self.highlight.extents[0] < xmin:
        extend_min = xmin
    if self.highlight.extents[1] > xmax:
        extend_max = xmax  
    self.highlight.extents = (extend_min, extend_max)

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
            canvas.top_right_axis.set_yscale(self.plot_settings.right_scale)          
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
    min_left = None
    max_left = None
    min_top = None
    max_top = None
    min_right = None
    max_right = None
    min_bottom = None
    max_bottom = None

    used_axes, item_list = get_used_axes(self)

    for axis in used_axes:
        if axis == "left":
            left_items = []
            for key in item_list["left"]:
                left_items.append(key)
            left_limits = find_limits(self, self.canvas.ax.get_yscale(), canvas, left_items)
        if axis == "right":
            right_items = []
            for key in item_list["right"]:
                right_items.append(key)
            right_limits = find_limits(self, self.canvas.right_axis.get_yscale(), canvas, right_items)
        if axis == "top":
            top_items = []
            for key in item_list["top"]:
                top_items.append(key)
            top_limits = find_limits(self, axis, canvas, top_items)
        if axis == "bottom":
            bottom_items = []
            for key in item_list["bottom"]:
                bottom_items.append(key)
            bottom_limits = find_limits(self, axis, canvas, bottom_items)
    if used_axes["left"] and used_axes["bottom"]:
        set_canvas_limits(self, left_limits, self.canvas.ax, axis_type = "Y")
        set_canvas_limits(self, bottom_limits, self.canvas.ax, axis_type = "X")
    if used_axes["left"] and used_axes["top"]:
        set_canvas_limits(self, left_limits, self.canvas.top_left_axis, axis_type = "Y")
        set_canvas_limits(self, top_limits, self.canvas.top_left_axis, axis_type = "X")
    if used_axes["right"] and used_axes["bottom"]:
        set_canvas_limits(self, right_limits, self.canvas.right_axis, axis_type = "Y")
        set_canvas_limits(self, bottom_limits, self.canvas.right_axis, axis_type = "X")
    if used_axes["right"] and used_axes["top"]:
        set_canvas_limits(self, right_limits, self.canvas.top_right_axis, axis_type = "Y")
        set_canvas_limits(self, top_limits, self.canvas.top_right_axis, axis_type = "X")

def get_used_axes(self):
    used_axis = dict()
    used_axis["left"] = False
    used_axis["right"] = False
    used_axis["top"] = False
    used_axis["bottom"] = False
    item_list = dict()
    left_items = []
    right_items = []
    top_items = []
    bottom_items = []

    for key, item in self.datadict.items():
        if item.plot_Y_position == "left":
            used_axis["left"] = True
            left_items.append(key)
        if item.plot_Y_position == "right":
            used_axis["right"] = True
            right_items.append(key)
        if item.plot_X_position == "top":
            used_axis["top"] = True
            top_items.append(key)
        if item.plot_X_position == "bottom":
            used_axis["bottom"] = True
            bottom_items.append(key)
    item_list["left"] = left_items
    item_list["right"] = right_items
    item_list["top"] = top_items
    item_list["bottom"] = bottom_items
    return used_axis, item_list

def set_canvas_limits(self, graph_limits, axis, axis_type, limits = {"xmin":None, "xmax":None, "ymin":None, "ymax":None}):
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
        if axis_type == "X":
            axis.set_xlim(graph_limits["xmin"], graph_limits["xmax"])
        if axis_type == "Y":
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

    for key in datadict:
        item = self.datadict[key]
        #Check the limits of each item, as long as it exists and it has the same axes as the one we're adjusting right now
        if item is not None and len(item.xdata) > 0:
            #Nonzero ydata is needed for logs
            nonzero_ydata = list(filter(lambda x: (x != 0), item.ydata))
            xmin_item = min(item.xdata)
            xmax_item = max(item.xdata)
            
            if axis == "log" and len(nonzero_ydata) > 0:
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
        graphs.open_selection_from_dict(self)
        if (not self.highlight == None):
            self.highlight.set_visible(False)
            self.highlight.set_active(False)
            self.highlight = None
        self.set_mode(None, None, self._mode)
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
    graphs.open_selection_from_dict(self)
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
    

def change_left_yscale(action, target, self):
    if target.get_string() == 'log':
        self.canvas.ax.set_yscale('log')
        self.plot_settings.yscale = "log"
    else:
        self.canvas.ax.set_yscale('linear')
        self.plot_settings.yscale = "linear"
    self.canvas.set_ticks(self)
    action.change_state(target)
    set_canvas_limits_axis(self, self.canvas)
    self.canvas.draw()

def change_right_yscale(action, target, self):
    if target.get_string() == 'log':
        self.canvas.top_right_axis.set_yscale('log')
        self.canvas.right_axis.set_yscale('log')
        self.plot_settings.right_scale = "log"
    else:
        self.canvas.top_right_axis.set_yscale('linear')
        self.canvas.right_axis.set_yscale('linear')
        self.plot_settings.right_scale = "linear"
    self.canvas.set_ticks(self)
    action.change_state(target)
    set_canvas_limits_axis(self, self.canvas)
    self.canvas.draw()

def change_top_xscale(action, target, self):
    if target.get_string() == 'log':
        self.canvas.top_left_axis.set_xscale('log')
        self.canvas.top_right_axis.set_xscale('log')
        self.plot_settings.top_scale = "log"
    else:
        self.canvas.top_left_axis.set_xscale('linear')
        self.canvas.top_right_axis.set_xscale('linear')
        self.plot_settings.top_scale = "linear"
    self.canvas.set_ticks(self)
    action.change_state(target)
    set_canvas_limits_axis(self, self.canvas)
    self.canvas.draw()

def change_bottom_xscale(action, target, self):
    if target.get_string() == 'log':
        self.canvas.ax.set_xscale('log')
        self.canvas.right_axis.set_xscale('log')
        self.plot_settings.xscale = "log"
    else:
        self.canvas.ax.set_xscale('linear')
        self.canvas.right_axis.set_xscale('linear')
        self.plot_settings.xscale = "linear"
    self.canvas.set_ticks(self)
    action.change_state(target)
    set_canvas_limits_axis(self, self.canvas)
    self.canvas.draw()

def restore_view(widget, shortcut, self):
    set_canvas_limits_axis(self, self.canvas)
    self.canvas.draw()

def view_back(widget, shortcut, self):
    self.dummy_toolbar._nav_stack.back()
    self.dummy_toolbar._update_view()

def view_forward(widget, shortcut, self):
    self.dummy_toolbar._nav_stack.forward()
    self.dummy_toolbar._update_view()

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
    used_colors = [colors.to_rgb(color) for color in used_colors]
    
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
            

# https://github.com/matplotlib/matplotlib/blob/c23ccdde6f0f8c071b09a88770e24452f2859e99/lib/matplotlib/backends/backend_gtk4.py#L306
def export_figure(widget, shortcut, self):
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
    def __init__(self, parent=None, xlabel="", ylabel="", yscale = "log", title="", scale="linear", style = "adwaita"):
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
            text_color = "white"
        else:
            self.figure.patch.set_facecolor("#fafafa")
            text_color = "black"
        params = {
        "font.weight": parent.plot_settings.font_weight,
        "font.sans-serif": parent.plot_settings.font_family,
        "font.size": parent.plot_settings.font_size,
        "axes.labelsize": parent.plot_settings.font_size,
        "xtick.labelsize": parent.plot_settings.font_size,
        "ytick.labelsize": parent.plot_settings.font_size,
        "axes.titlesize": parent.plot_settings.font_size,
        "legend.fontsize": parent.plot_settings.font_size,
        "font.style": parent.plot_settings.font_style,
        "mathtext.default": "regular",
        "xtick.color" : text_color,
        "ytick.color" : text_color,
        "axes.labelcolor" : text_color,
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

    def _post_draw(self, widget, context):
        """
        Override with custom implementation of rubberband to allow for custom rubberband style
        @param context: https://pycairo.readthedocs.io/en/latest/reference/context.html
        """
        if self._rubberband_rect is None:
            return

        lw = 1
        if not self._context_is_scaled:
            x0, y0, w, h = (dim / self.device_pixel_ratio
                            for dim in self._rubberband_rect)
        else:
            x0, y0, w, h = self._rubberband_rect
            lw *= self.device_pixel_ratio
        x1 = x0 + w
        y1 = y0 + h

        context.set_antialias(1)
        context.set_line_width(lw)
        context.rectangle(x0, y0, w, h)
        #input are floats so divide rgb value by 255
        context.set_source_rgba(120 / 255, 174 / 255, 237 / 255, 0.2)
        context.fill()
        context.rectangle(x0, y0, w, h)
        context.set_source_rgba(120 / 255, 174 / 255, 237 / 255, 1)
        context.stroke()
