# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from graphs import graphs, utilities

from matplotlib import pyplot


def set_limit_padding(axis_direction, axis):
    """Apply some padding to the limits on the axes."""
    # Update graph limits with limits that were given as argument
    xmin = min(axis.get_xlim())
    xmax = max(axis.get_xlim())
    ymin = min(axis.get_ylim())
    ymax = max(axis.get_ylim())
    x_span = xmax - xmin
    y_span = ymax - ymin
    if axis.get_xscale() == "linear":
        xmin -= 0.015 * x_span
        xmax += 0.015 * x_span
    if axis.get_yscale() == "linear":
        if y_span != 0:
            if ymin > 0:
                ymin *= 0.95
            else:
                ymin *= 1.05
            ymax *= 1.05
        else:
            ymax += abs(ymax * 0.05)
            ymin -= abs(ymin * 0.05)
    else:
        ymin *= 0.5
        ymax *= 2
    try:
        xmin = utilities.sig_fig_round(xmin, 3)
        xmax = utilities.sig_fig_round(xmax, 3)
        ymin = utilities.sig_fig_round(ymin, 3)
        ymax = utilities.sig_fig_round(ymax, 3)
        if axis_direction in ["left", "right"]:
            axis.set_ylim(ymin, ymax)
        if axis_direction in ["top", "bottom"]:
            axis.set_xlim(xmin, xmax)
    except ValueError:
        logging.error(
            "Could not set limits, one of the values was probably infinite")


def find_min_max(axis, items, axis_type):
    """Find min and max value on a given axis, skip zeroes for log scale."""
    min_all = None
    max_all = None

    for item in items:
        if axis_type == "X":
            data = item.xdata
            scale = axis.get_xscale()
        elif axis_type == "Y":
            data = item.ydata
            scale = axis.get_yscale()

        nonzero_data = list(filter(lambda x: (x != 0), data))
        if scale == "log" and len(nonzero_data) > 0:
            min_item = min(nonzero_data)
        else:
            min_item = min(data)
        max_item = max(data)
        if min_all is None:
            min_all = min_item
        if max_all is None:
            max_all = max_item
        if min_item < min_all:
            min_all = min_item
        if max_item > max_all:
            max_all = max_item

    return min_all, max_all


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
    self.canvas.axis.set_yscale(target.get_string())
    self.canvas.top_left_axis.set_yscale(target.get_string())
    self.plot_settings.yscale = target.get_string()
    action.change_state(target)
    graphs.refresh(self, set_limits=True)


def change_right_yscale(action, target, self):
    self.canvas.top_right_axis.set_yscale(target.get_string())
    self.canvas.right_axis.set_yscale(target.get_string())
    self.plot_settings.right_scale = target.get_string()
    action.change_state(target)
    graphs.refresh(self, set_limits=True)


def change_top_xscale(action, target, self):
    self.canvas.top_left_axis.set_xscale(target.get_string())
    self.canvas.top_right_axis.set_xscale(target.get_string())
    self.plot_settings.top_scale = target.get_string()
    action.change_state(target)
    graphs.refresh(self, set_limits=True)


def change_bottom_xscale(action, target, self):
    self.canvas.axis.set_xscale(target.get_string())
    self.canvas.right_axis.set_xscale(target.get_string())
    self.plot_settings.xscale = target.get_string()
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
