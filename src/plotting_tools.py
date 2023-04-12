# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from graphs import graphs, utilities

from matplotlib import pyplot


def set_axis_limits(graph_limits, axis, axis_type, limits=None):
    """Set an calculate the canvas limits for a given axis."""
    if not limits:
        limits = {"xmin": None, "xmax": None, "ymin": None, "ymax": None}
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
            xmin = utilities.sig_fig_round(graph_limits["xmin"], 3)
            xmax = utilities.sig_fig_round(graph_limits["xmax"], 3)
            axis.set_xlim(xmin, xmax)
        if axis_type == "Y":
            ymin = utilities.sig_fig_round(graph_limits["ymin"], 3)
            ymax = utilities.sig_fig_round(graph_limits["ymax"], 3)
            axis.set_ylim(ymin, ymax)
    except ValueError:
        logging.error(
            "Could not set limits, one of the values was probably infinite")


def find_limits(scale, items):
    """Find the limits that are to be used for the axes."""
    xmin_all = None
    xmax_all = None
    ymin_all = None
    ymax_all = None

    for item in items:
        # Check the limits of each item, as long as it exists and it has the
        # same axes as the one we"re adjusting right now
        if item is not None and len(item.xdata) > 0:
            # Nonzero ydata is needed for logs
            nonzero_ydata = list(filter(lambda x: (x != 0), item.ydata))
            xmin_item = min(item.xdata)
            xmax_item = max(item.xdata)

            if scale == "log" and len(nonzero_ydata) > 0:
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
    for axis in [canvas.axis, canvas.right_axis,
                 canvas.top_left_axis, canvas.top_right_axis]:
        axis.get_xaxis().set_visible(False)
        axis.get_yaxis().set_visible(False)
    used_axes = utilities.get_used_axes(self)[0]
    if used_axes["left"]:
        canvas.top_left_axis.get_yaxis().set_visible(True)
        canvas.axis.get_yaxis().set_visible(True)
    if used_axes["right"]:
        canvas.top_right_axis.get_yaxis().set_visible(True)
        canvas.right_axis.get_yaxis().set_visible(True)
    if used_axes["top"]:
        canvas.top_right_axis.get_xaxis().set_visible(True)
        canvas.top_left_axis.get_xaxis().set_visible(True)
    if used_axes["bottom"]:
        canvas.axis.get_xaxis().set_visible(True)
        canvas.right_axis.get_xaxis().set_visible(True)

    canvas.top_right_axis.get_xaxis().set_visible(False)
    canvas.right_axis.get_xaxis().set_visible(False)
    canvas.top_right_axis.get_yaxis().set_visible(False)
    canvas.top_left_axis.get_yaxis().set_visible(False)


def change_left_yscale(action, target, self):
    if target.get_string() == "log":
        self.canvas.axis.set_yscale("log")
        self.canvas.top_left_axis.set_yscale("log")
        self.plot_settings.yscale = "log"
    else:
        self.canvas.axis.set_yscale("linear")
        self.canvas.top_left_axis.set_yscale("linear")
        self.plot_settings.yscale = "linear"
    action.change_state(target)
    graphs.refresh(self, set_limits=True)


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
    graphs.refresh(self, set_limits=True)


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
    graphs.refresh(self, set_limits=True)


def change_bottom_xscale(action, target, self):
    if target.get_string() == "log":
        self.canvas.axis.set_xscale("log")
        self.canvas.right_axis.set_xscale("log")
        self.plot_settings.xscale = "log"
    else:
        self.canvas.axis.set_xscale("linear")
        self.canvas.right_axis.set_xscale("linear")
        self.plot_settings.xscale = "linear"
    action.change_state(target)
    graphs.refresh(self, set_limits=True)


def get_next_color(self):
    """Get the color that is to be used for the next data set"""
    color_cycle = pyplot.rcParams["axes.prop_cycle"].by_key()["color"]
    used_colors = []
    for item in self.datadict.values():
        used_colors.append(item.color)
        # If we've got all colors once, remove those from used_colors so we
        # can loop around
        if set(used_colors) == set(color_cycle):
            for color in color_cycle:
                used_colors.remove(color)

    for color in color_cycle:
        if color not in used_colors:
            return color
