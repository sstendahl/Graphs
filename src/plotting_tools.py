# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from graphs import graphs


def get_used_axes(self):
    used_axis = {
        "left": False,
        "right": False,
        "top": False,
        "bottom": False
    }
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


def set_canvas_limits(graph_limits, axis, axis_type,
                      limits={"xmin": None, "xmax": None,
                              "ymin": None, "ymax": None}):
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
        logging.error(
            "Could not set limits, one of the values was probably infinite")


def find_limits(self, axis, datadict):
    """Find the limits that are to be used for the axes."""
    xmin_all = None
    xmax_all = None
    ymin_all = None
    ymax_all = None

    for key in datadict:
        item = self.datadict[key]
        # Check the limits of each item, as long as it exists and it has the
        # same axes as the one we"re adjusting right now
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
    return {
        "xmin": xmin_all,
        "xmax": xmax_all,
        "ymin": ymin_all,
        "ymax": ymax_all}


def hide_unused_axes(self, canvas):
    """
    Hide axes that are not in use,
    to avoid unnecessary ticks in the plots.
    """
    # Double check the code here, seems to work but this is too messy
    for axis in [canvas.ax, canvas.right_axis,
                 canvas.top_left_axis, canvas.top_right_axis]:
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
    action.change_state(target)
    graphs.refresh(self, set_limits = True)


def change_right_yscale(action, target, self):
    if target.get_string() == "log":
        self.canvas.top_right_axis.set_yscale("log")
        self.canvas.right_axis.set_yscale("log")
        self.plot_settings.right_scale = "log"
    else:
        self.canvas.top_right_axis.set_yscale("linear")
        self.canvas.right_axis.set_yscale("linear")
        self.plot_settings.right_scale = "linear"
    action.change_state(target)
    graphs.refresh(self, set_limits = True)


def change_top_xscale(action, target, self):
    if target.get_string() == "log":
        self.canvas.top_left_axis.set_xscale("log")
        self.canvas.top_right_axis.set_xscale("log")
        self.plot_settings.top_scale = "log"
    else:
        self.canvas.top_left_axis.set_xscale("linear")
        self.canvas.top_right_axis.set_xscale("linear")
        self.plot_settings.top_scale = "linear"
    action.change_state(target)
    graphs.refresh(self, set_limits = True)


def change_bottom_xscale(action, target, self):
    if target.get_string() == "log":
        self.canvas.ax.set_xscale("log")
        self.canvas.right_axis.set_xscale("log")
        self.plot_settings.xscale = "log"
    else:
        self.canvas.ax.set_xscale("linear")
        self.canvas.right_axis.set_xscale("linear")
        self.plot_settings.xscale = "linear"
    action.change_state(target)
    graphs.refresh(self, set_limits = True)


def get_next_color(self):
    """Get the color that is to be used for the next data set"""
    color_list = self.canvas.color_cycle
    used_colors = []
    for _key, item in self.datadict.items():
        used_colors.append(item.color)

    for color in color_list:
        if color not in used_colors:
            return color
    return None
