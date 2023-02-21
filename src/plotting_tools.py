# SPDX-License-Identifier: GPL-3.0-or-later
import copy

from gi.repository import Adw

from graphs import graphs, utilities

import matplotlib.font_manager
from matplotlib import colors
from matplotlib.widgets import SpanSelector


def define_highlight(self, span=None):
    """
    Create a span selector object, to highlight part of the graph.
    If a span already exists, make it visible instead
    """
    color = utilities.lookup_color(self, "accent_color")
    self.highlight = SpanSelector(
        self.canvas.top_right_axis,
        lambda x, y: on_highlight_define(self),
        "horizontal",
        useblit=True,
        props={"facecolor": (color.red, color.green, color.blue, 0.3), "edgecolor": (color.red, color.green, color.blue, 1), "linewidth": 1},
        handle_props={"linewidth": 0},
        interactive=True,
        drag_from_anywhere=True)
    if span is not None:
        self.highlight.extents = span


def on_highlight_define(self):
    """
    This ensures that the span selector doesn"t go out of range
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


def plot_figure(self, canvas, x_data, y_data, filename="", linewidth=2, marker=None, linestyle="solid",
                color=None, marker_size=10, y_axis="left", x_axis="bottom"):
    """
    Plot the figure on the graph
    Necessary input arguments are self, the canvas to plot the figure on and the
    X and Y data
    """
    if y_axis == "left":
        if x_axis == "bottom":
            canvas.ax.plot(x_data, y_data, linewidth=linewidth, label=filename, linestyle=linestyle, marker=marker, color=color, markersize=marker_size)
        elif x_axis == "top":
            canvas.top_left_axis.plot(x_data, y_data, linewidth=linewidth, label=filename, linestyle=linestyle, marker=marker, color=color, markersize=marker_size)
    elif y_axis == "right":
        if x_axis == "bottom":
            canvas.right_axis.plot(x_data, y_data, linewidth=linewidth, label=filename, linestyle=linestyle, marker=marker, color=color, markersize=marker_size)
        elif x_axis == "top":
            canvas.top_right_axis.plot(x_data, y_data, linewidth=linewidth, label=filename, linestyle=linestyle, marker=marker, color=color, markersize=marker_size)
            canvas.top_right_axis.set_yscale(self.plot_settings.right_scale)
    set_legend(self, canvas)


def set_legend(self, canvas):
    """Set the legend of the graph"""
    if self.plot_settings.legend:
        canvas.legends = []
        lines, labels = canvas.ax.get_legend_handles_labels()
        lines2, labels2 = canvas.right_axis.get_legend_handles_labels()
        lines3, labels3 = canvas.top_left_axis.get_legend_handles_labels()
        lines4, labels4 = canvas.top_right_axis.get_legend_handles_labels()
        canvas.top_right_axis.legend(lines + lines2 + lines3 + lines4, labels + labels2 + labels3 + labels4, loc=0, frameon=True)


def set_canvas_limits_axis(self):
    """Set the canvas limits for each axis that is present"""
    used_axes, item_list = get_used_axes(self)

    for axis in used_axes:
        if axis == "left":
            left_items = []
            for key in item_list["left"]:
                left_items.append(key)
            left_limits = find_limits(self, self.canvas.ax.get_yscale(), left_items)
        if axis == "right":
            right_items = []
            for key in item_list["right"]:
                right_items.append(key)
            right_limits = find_limits(self, self.canvas.right_axis.get_yscale(), right_items)
        if axis == "top":
            top_items = []
            for key in item_list["top"]:
                top_items.append(key)
            top_limits = find_limits(self, axis, top_items)
        if axis == "bottom":
            bottom_items = []
            for key in item_list["bottom"]:
                bottom_items.append(key)
            bottom_limits = find_limits(self, axis, bottom_items)
    if used_axes["left"] and used_axes["bottom"]:
        set_canvas_limits(left_limits, self.canvas.ax, axis_type="Y")
        set_canvas_limits(bottom_limits, self.canvas.ax, axis_type="X")
    if used_axes["left"] and used_axes["top"]:
        set_canvas_limits(left_limits, self.canvas.top_left_axis, axis_type="Y")
        set_canvas_limits(top_limits, self.canvas.top_left_axis, axis_type="X")
    if used_axes["right"] and used_axes["bottom"]:
        set_canvas_limits(right_limits, self.canvas.right_axis, axis_type="Y")
        set_canvas_limits(bottom_limits, self.canvas.right_axis, axis_type="X")
    if used_axes["right"] and used_axes["top"]:
        set_canvas_limits(right_limits, self.canvas.top_right_axis, axis_type="Y")
        set_canvas_limits(top_limits, self.canvas.top_right_axis, axis_type="X")


def get_used_axes(self):
    used_axis = {}
    used_axis["left"] = False
    used_axis["right"] = False
    used_axis["top"] = False
    used_axis["bottom"] = False
    item_list = {}
    left_items = []
    right_items = []
    top_items = []
    bottom_items = []

    for key, item in self.datadict.items():
        if item.plot_y_position == "left":
            used_axis["left"] = True
            left_items.append(key)
        if item.plot_y_position == "right":
            used_axis["right"] = True
            right_items.append(key)
        if item.plot_x_position == "top":
            used_axis["top"] = True
            top_items.append(key)
        if item.plot_x_position == "bottom":
            used_axis["bottom"] = True
            bottom_items.append(key)
    item_list["left"] = left_items
    item_list["right"] = right_items
    item_list["top"] = top_items
    item_list["bottom"] = bottom_items
    return used_axis, item_list


def set_canvas_limits(graph_limits, axis, axis_type, limits={"xmin": None, "xmax": None, "ymin": None, "ymax": None}):
    """Set an calculate the canvas limits for a given axis."""
    # Update graph limits with limits that were given as argument
    for key, item in limits.items():
        if item is not None:
            graph_limits[key] = item
    x_span = (graph_limits["xmax"] - graph_limits["xmin"])
    y_span = (graph_limits["ymax"] - graph_limits["ymin"])
    if axis.get_xscale() == "linear":
        graph_limits["xmin"] -= 0.015 * x_span
        graph_limits["xmax"] += 0.015 * x_span
    if axis.get_yscale() == "linear":
        if y_span != 0:
            if graph_limits["ymin"] > 0:
                graph_limits["ymin"] *= 0.95
            else:
                graph_limits["ymin"] *= 1.05
            graph_limits["ymax"] *= 1.05
        else:
            graph_limits["ymax"] += abs(graph_limits["ymax"] * 0.05)
            graph_limits["ymin"] -= abs(graph_limits["ymin"] * 0.05)
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


def find_limits(self, axis, datadict):
    """Find the limits that are to be used for the axes."""
    xmin_all = None
    xmax_all = None
    ymin_all = None
    ymax_all = None

    for key in datadict:
        item = self.datadict[key]
        # Check the limits of each item, as long as it exists and it has the same axes as the one we"re adjusting right now
        if item is not None and len(item.xdata) > 0:
            # Nonzero ydata is needed for logs
            nonzero_ydata = list(filter(lambda x: (x != 0), item.ydata))
            xmin_item = min(item.xdata)
            xmax_item = max(item.xdata)

            if axis == "log" and len(nonzero_ydata) > 0:
                ymin_item = min(nonzero_ydata)
            else:
                ymin_item = min(item.ydata)
            ymax_item = max(item.ydata)

            if xmin_all is None:
                xmin_all = xmin_item
            if xmax_all is None:
                xmax_all = xmax_item
            if ymin_all is None:
                ymin_all = ymin_item
            if ymax_all is None:
                ymax_all = ymax_item
            if xmin_item < xmin_all:
                xmin_all = xmin_item
            if xmax_item > xmax_all:
                xmax_all = xmax_item
            if (ymin_item < ymin_all):
                ymin_all = ymin_item
            if ymax_item > ymax_all:
                ymax_all = ymax_item
    return {"xmin": xmin_all, "xmax": xmax_all, "ymin": ymin_all, "ymax": ymax_all}


def reload_plot(self):
    """Completely reload the plot of the graph"""
    graphs.load_empty(self)
    if len(self.datadict) > 0:
        hide_unused_axes(self, self.canvas)
        graphs.open_selection_from_dict(self)
        if self.highlight is not None:
            self.highlight.set_visible(False)
            self.highlight.set_active(False)
            self.highlight = None
        self.set_mode(None, None, self.interaction_mode)
        set_canvas_limits_axis(self)
    self.canvas.grab_focus()


def refresh_plot(self, canvas=None, set_limits=True):
    """Refresh the graph without completely reloading it."""
    if canvas is None:
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
        set_canvas_limits_axis(self)
    self.canvas.draw()


def hide_unused_axes(self, canvas):
    """Hide axes that are not in use, to avoid unnecessary ticks in the plots."""
    # Double check the code here, seems to work but this is too messy
    for axis in [canvas.ax, canvas.right_axis, canvas.top_left_axis, canvas.top_right_axis]:
        axis.get_xaxis().set_visible(True)
        axis.get_yaxis().set_visible(True)
    left = False
    right = False
    top = False
    bottom = False
    for _key, item in self.datadict.items():
        if item.plot_y_position == "left":
            left = True
        if item.plot_y_position == "right":
            right = True
        if item.plot_x_position == "top":
            top = True
        if item.plot_x_position == "bottom":
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
    if target.get_string() == "log":
        self.canvas.ax.set_yscale("log")
        self.plot_settings.yscale = "log"
    else:
        self.canvas.ax.set_yscale("linear")
        self.plot_settings.yscale = "linear"
    self.canvas.set_ticks(self)
    action.change_state(target)
    set_canvas_limits_axis(self)
    self.canvas.draw()


def change_right_yscale(action, target, self):
    if target.get_string() == "log":
        self.canvas.top_right_axis.set_yscale("log")
        self.canvas.right_axis.set_yscale("log")
        self.plot_settings.right_scale = "log"
    else:
        self.canvas.top_right_axis.set_yscale("linear")
        self.canvas.right_axis.set_yscale("linear")
        self.plot_settings.right_scale = "linear"
    self.canvas.set_ticks(self)
    action.change_state(target)
    set_canvas_limits_axis(self)
    self.canvas.draw()


def change_top_xscale(action, target, self):
    if target.get_string() == "log":
        self.canvas.top_left_axis.set_xscale("log")
        self.canvas.top_right_axis.set_xscale("log")
        self.plot_settings.top_scale = "log"
    else:
        self.canvas.top_left_axis.set_xscale("linear")
        self.canvas.top_right_axis.set_xscale("linear")
        self.plot_settings.top_scale = "linear"
    self.canvas.set_ticks(self)
    action.change_state(target)
    set_canvas_limits_axis(self)
    self.canvas.draw()


def change_bottom_xscale(action, target, self):
    if target.get_string() == "log":
        self.canvas.ax.set_xscale("log")
        self.canvas.right_axis.set_xscale("log")
        self.plot_settings.xscale = "log"
    else:
        self.canvas.ax.set_xscale("linear")
        self.canvas.right_axis.set_xscale("linear")
        self.plot_settings.xscale = "linear"
    self.canvas.set_ticks(self)
    action.change_state(target)
    set_canvas_limits_axis(self)
    self.canvas.draw()


def get_next_color(self):
    """Get the color that is to be used for the next data set"""
    color_list = self.canvas.color_cycle
    used_colors = []
    item_rows = copy.copy(self.item_rows)
    color_length = len(color_list)
    if len(item_rows) >= color_length:
        item_rows_list = list(item_rows.items())
        item_rows_list = item_rows_list[- color_length + 1:]
        item_rows = dict(item_rows_list)
    for _key, item in item_rows.items():
        used_colors.append(item.color_picker.color)
    used_colors = [colors.to_rgb(color) for color in used_colors]

    for color in color_list:
        if color not in used_colors:
            return color
    return None


def load_fonts():
    """Load system fonts that are installed on the system"""
    font_list = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
    for font in font_list:
        try:
            matplotlib.font_manager.fontManager.addfont(font)
        except Exception:
            print(f"Could not load {font}")


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
