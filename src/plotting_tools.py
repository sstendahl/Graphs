# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib

from graphs import graphs, utilities
from graphs.item import Item

from matplotlib import pyplot


def optimize_limits(self):
    with contextlib.suppress(KeyError):
        self.Clipboard.clipboard[self.Clipboard.clipboard_pos]["view"] = \
            self.canvas.limits
    used_axes, items = utilities.get_used_axes(self)
    axis_map = {
        "left": self.canvas.axis,
        "right": self.canvas.right_axis,
        "top": self.canvas.top_left_axis,
        "bottom": self.canvas.axis,
    }

    limits = {
        "min_bottom": self.plot_settings.min_bottom,
        "max_bottom": self.plot_settings.max_bottom,
        "min_top": self.plot_settings.min_top,
        "max_top": self.plot_settings.max_top,
        "min_left": self.plot_settings.min_left,
        "max_left": self.plot_settings.max_left,
        "min_right": self.plot_settings.min_right,
        "max_right": self.plot_settings.max_right,
    }
    for direction, used in used_axes.items():
        if not used:
            continue
        if direction in ["top", "bottom"]:
            scale = axis_map[direction].get_xscale()
            datalist = [item.xdata for item in items[direction]
                        if isinstance(item, Item)]
        elif direction in ["left", "right"]:
            scale = axis_map[direction].get_yscale()
            datalist = [item.ydata for item in items[direction]
                        if isinstance(item, Item)]
        min_all, max_all = [], []
        for data in datalist:
            nonzero_data = list(filter(lambda x: (x != 0), data))
            if scale == "log" and len(nonzero_data) > 0:
                min_all.append(min(nonzero_data))
            else:
                min_all.append(min(data))
            max_all.append(max(data))
        min_all = min(min_all)
        max_all = max(max_all)
        span = max_all - min_all
        if scale == "linear":
            if direction in ["left", "right"]:
                padding_factor = 0.05
            else:
                padding_factor = 0.015
            min_all -= padding_factor * span
            max_all += padding_factor * span
        elif direction in ["left", "right"]:
            min_all *= 0.5
            max_all *= 2
        limits[f"min_{direction}"] = min_all
        limits[f"max_{direction}"] = max_all
    self.canvas.limits = limits
    self.canvas.apply_limits()


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
        canvas.axis.get_yaxis().set_visible(True)
    if used_axes["right"]:
        canvas.right_axis.get_yaxis().set_visible(True)
    if used_axes["top"]:
        canvas.top_left_axis.get_xaxis().set_visible(True)
    if used_axes["bottom"]:
        canvas.axis.get_xaxis().set_visible(True)


def _change_scale(self, action, target):
    action.change_state(target)
    graphs.refresh(self)
    optimize_limits(self)
    self.ViewClipboard.add()


def change_left_scale(action, target, self):
    self.canvas.axis.set_yscale(target.get_string())
    self.canvas.top_left_axis.set_yscale(target.get_string())
    self.plot_settings.left_scale = target.get_string()
    _change_scale(self, action, target)


def change_right_scale(action, target, self):
    self.canvas.top_right_axis.set_yscale(target.get_string())
    self.canvas.right_axis.set_yscale(target.get_string())
    self.plot_settings.right_scale = target.get_string()
    _change_scale(self, action, target)


def change_top_scale(action, target, self):
    self.canvas.top_left_axis.set_xscale(target.get_string())
    self.canvas.top_right_axis.set_xscale(target.get_string())
    self.plot_settings.top_scale = target.get_string()
    _change_scale(self, action, target)


def change_bottom_scale(action, target, self):
    self.canvas.axis.set_xscale(target.get_string())
    self.canvas.right_axis.set_xscale(target.get_string())
    self.plot_settings.bottom_scale = target.get_string()
    _change_scale(self, action, target)


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
