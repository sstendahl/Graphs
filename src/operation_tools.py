# SPDX-License-Identifier: GPL-3.0-or-later
from graphs.data import Data

import numpy


def select_data(self, keys):
    """
    Select data that is highlighted by the span
    Basically just creates new data_sets with the key "_selected" appended
    """
    # First delete previously selected data
    delete_selected(self)
    selected_dict = {}
    start_stop = {}

    for key in keys:
        item = self.datadict[key]
        highlight = self.canvas.highlight
        startx = min(highlight.extents)
        stopx = max(highlight.extents)
        start_index = 0
        stop_index = 0
        # Selection is different for bottom and top axis. The span selector
        # takes the top axis coordinates. So for the data that uses the bottom
        # axis as x-axis coordinates, the coordinates first
        # needs to be converted.
        if item.plot_x_position == "bottom":
            xrange_bottom = max(self.canvas.ax.get_xlim()) \
                - min(self.canvas.ax.get_xlim())
            xrange_top = max(self.canvas.top_left_axis.get_xlim()) \
                - min(self.canvas.top_left_axis.get_xlim())
            # Run into issues if the range is different, so we calculate this
            # by getting what fraction of top axis is highlighted
            if self.canvas.top_left_axis.get_xscale() == "log":
                fraction_left_limit = get_fraction_at_value(
                    min(highlight.extents),
                    min(self.canvas.top_left_axis.get_xlim()),
                    max(self.canvas.top_left_axis.get_xlim()))
                fraction_right_limit = get_fraction_at_value(
                    max(highlight.extents),
                    min(self.canvas.top_left_axis.get_xlim()),
                    max(self.canvas.top_left_axis.get_xlim()))
            elif self.canvas.top_left_axis.get_xscale() == "linear":
                fraction_left_limit = (
                    min(highlight.extents) - min(
                        self.canvas.top_left_axis.get_xlim())) / (xrange_top)
                fraction_right_limit = (
                    max(highlight.extents) - min(
                        self.canvas.top_left_axis.get_xlim())) / (xrange_top)

            # Use the fraction that is higlighted on top to calculate to what
            # values this corresponds on bottom axis
            if self.canvas.ax.get_xscale() == "log":
                startx = get_value_at_fraction(
                    fraction_left_limit,
                    min(self.canvas.ax.get_xlim()),
                    max(self.canvas.ax.get_xlim()))
                stopx = get_value_at_fraction(
                    fraction_right_limit,
                    min(self.canvas.ax.get_xlim()),
                    max(self.canvas.ax.get_xlim()))
            elif self.canvas.ax.get_xscale() == "linear":
                xlim = min(self.canvas.ax.get_xlim())
                startx = xlim + xrange_bottom * fraction_left_limit
                stopx = xlim + xrange_bottom * fraction_right_limit
        # If startx and stopx are not out of range, that is,
        # if the sample data is within the highlight
        if not ((startx < min(item.xdata) and stopx < min(item.xdata)) or (
                startx > max(item.xdata))):
            selected_data, start_index, stop_index = pick_data_selection(
                self, item, startx, stopx)
            selected_dict[f"{key}_selected"] = selected_data
        if (startx < min(item.xdata) and stopx < min(item.xdata)) \
                or (startx > max(item.xdata)):
            for key in self.datadict.copy():
                if key.endswith("_selected"):
                    del (self.datadict[key])
        # Update the dataset to include the selected data, only if we actually
        # managed to select data.
        if len(selected_dict) > 0:
            self.datadict.update(selected_dict)
        start_stop[key] = [start_index, stop_index]
    return start_stop


def get_value_at_fraction(fraction, start, end):
    """
    Obtain the selected value of an axis given at which percentage (in terms of
    fraction) of the length this axis is selected given the start and end range
    of this axis
    """
    log_start = numpy.log10(start)
    log_end = numpy.log10(end)
    log_range = log_end - log_start
    log_value = log_start + log_range * fraction
    return pow(10, log_value)


def get_fraction_at_value(value, start, end):
    """
    Obtain the fraction of the total length of the selected axis a specific
    value corresponds to given the start and end range of the axis.
    """
    log_start = numpy.log10(start)
    log_end = numpy.log10(end)
    log_value = numpy.log10(value)
    log_range = log_end - log_start
    return (log_value - log_start) / log_range


def pick_data_selection(self, item, startx, stopx):
    """
    Checks for a given item if it is within the selected span. If it is, it
    returns the part of the data that is within the span.
    """
    xdata = item.xdata
    ydata = item.ydata
    xdata, ydata = sort_data(xdata, ydata)
    start_index = 0
    stop_index = len(xdata)
    found_start = False
    found_stop = False
    for index, value in enumerate(xdata):
        if value > startx and not found_start:
            start_index = index
            found_start = True
        if value > stopx and not found_stop:
            stop_index = index
            found_stop = True
    selected_data = Data(self, xdata[start_index:stop_index],
                         ydata[start_index:stop_index])
    if len(selected_data.xdata) > 0 and (found_start or found_stop):
        return selected_data, start_index, stop_index
    return None


def sort_data(x_values, y_values):
    """
    Sort x and y-coordinates such that the x-data is continiously increasing
    Takes in x, and y coordinates of that array, and returns the sorted variant
    """
    zipped_list = zip(x_values, y_values)
    sorted_lists = sorted(zipped_list, key=lambda x_values: x_values[0])
    sorted_x, sorted_y = zip(*sorted_lists)
    return list(sorted_x), list(sorted_y)


def delete_selected(self):
    for key in self.datadict.copy():
        if key.endswith("_selected"):
            del (self.datadict[key])
