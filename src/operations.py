# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from graphs import calculation, clipboard, graphs, plotting_tools, utilities
from graphs.data import Data
from graphs.misc import InteractionMode

import numpy

from scipy import integrate


def get_item(self, key):
    """
    Retrieve item from datadict with start and stop index.
    If interaction_mode is set to "SELECT"
    """
    item = self.datadict[key]
    start_index = 0
    stop_index = len(item.xdata)
    if self.interaction_mode == InteractionMode.SELECT:
        startx, stopx = self.canvas.highlight.get_start_stop(
            item.plot_x_position == "bottom")

        # If startx and stopx are not out of range, that is,
        # if the sample data is within the highlight
        if not ((startx < min(item.xdata) and stopx < min(item.xdata)) or (
                startx > max(item.xdata))):
            new_x, new_y = sort_data(item.xdata, item.ydata)
            found_start = False
            found_stop = False
            for index, value in enumerate(item.xdata):
                if value > startx and not found_start:
                    start_index = index
                    found_start = True
                if value > stopx and not found_stop:
                    stop_index = index
                    found_stop = True
            item = Data(
                self,
                new_x[start_index:stop_index],
                new_y[start_index:stop_index])
        else:
            item = None
            start_index = None
            stop_index = None
    return item, start_index, stop_index


def sort_data(xdata, ydata):
    sorted_lists = sorted(
        zip(xdata, ydata), key=lambda x_values: x_values[0])
    sorted_x, sorted_y = zip(*sorted_lists)
    return list(sorted_x), list(sorted_y)


def operation(self, callback, *args):
    try:
        keys = utilities.get_selected_keys(self)
        for key in keys:
            item, start_index, stop_index = get_item(self, key)
            if item is not None:
                xdata, ydata, sort = callback(self, item, *args)
                self.datadict[key].xdata[start_index:stop_index] = xdata
                self.datadict[key].ydata[start_index:stop_index] = ydata
                if sort:
                    sort_data(
                        self.datadict[key].xdata, self.datadict[key].ydata)
        clipboard.add(self)
        plotting_tools.refresh_plot(self)
    except Exception:
        message = "Couldn't perform operation"
        self.main_window.add_toast(message)
        logging.exception(message)


def translate_x(self, item, offset):
    """
    Translate all selected data on the x-axis
    Amount to be shifted is equal to the value in the translate_x entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return [value + offset for value in item.xdata], item.ydata, True


def translate_y(self, item, offset):
    """
    Translate all selected data on the y-axis
    Amount to be shifted is equal to the value in the translate_y entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return item.xdata, [value + offset for value in item.ydata], False


def multiply_x(self, item, multiplier):
    """
    Multiply all selected data on the x-axis
    Amount to be shifted is equal to the value in the multiply_x entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return [value * multiplier for value in item.xdata], item.ydata, True


def multiply_y(self, item, multiplier):
    """
    Multiply all selected data on the y-axis
    Amount to be shifted is equal to the value in the multiply_y entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return item.xdata, [value * multiplier for value in item.ydata], False


def normalize(self, item):
    """Normalize all selected data"""
    return item.xdata, [value / max(item.ydata) for value in item.ydata], False


def smoothen(self, item):
    """Smoothen y-data."""
    box_points = 4
    box = numpy.ones(box_points) / box_points
    new_ydata = numpy.convolve(item.ydata, box, mode="same")
    return item.xdata, new_ydata, False


def center(self, item):
    """
    Center all selected data
    Depending on the key, will center either on the middle coordinate, or on
    the maximum value of the data
    """
    if self.preferences.config["action_center_data"] == \
            "Center at maximum Y value":
        middle_index = item.ydata.index(max(item.ydata))
        middle_value = item.xdata[middle_index]
    elif self.preferences.config["action_center_data"] == \
            "Center at middle coordinate":
        middle_value = (min(item.xdata) + max(item.xdata)) / 2
    new_xdata = [coordinate - middle_value for coordinate in item.xdata]
    return new_xdata, item.ydata, True


def shift_vertically(self, item,
                     shift_value_log=1, shift_value_linear=0):
    """
    Shifts data vertically with respect to each other
    By default it scales linear data by 1.5 times the total span of the
    ydata, and log data by a factor of 10000.
    """
    ymin = min(x for x in item.ydata if x != 0)
    ymax = max(x for x in item.ydata if x != 0)
    shift_value_linear += 1.2 * (ymax - ymin)
    shift_value_log *= 10 ** (numpy.log10(ymax / ymin))
    if item.plot_y_position == "left":
        if self.plot_settings.yscale == "log":
            new_ydata = [value * shift_value_log for value in item.ydata]
        if self.plot_settings.yscale == "linear":
            new_ydata = [value + shift_value_linear for value in item.ydata]
    if item.plot_y_position == "right":
        if self.plot_settings.right_scale == "log":
            new_ydata = [value * shift_value_log for value in item.ydata]
        if self.plot_settings.right_scale == "linear":
            new_ydata = [value + shift_value_linear for value in item.ydata]
    return item.xdata, new_ydata, False


def cut_selected(self, item):
    """Cut selected data over the span that is selected"""
    return [], [], False


def get_derivative(self, item):
    """Calculate derivative of all selected data"""
    x_values = numpy.array(item.xdata)
    y_values = numpy.array(item.ydata)
    dy_dx = numpy.gradient(y_values, x_values)
    return item.xdata, dy_dx.tolist(), False


def get_integral(self, item):
    """Calculate indefinite integral of all selected data"""
    x_values = numpy.array(item.xdata)
    y_values = numpy.array(item.ydata)
    indefinite_integral = integrate.cumtrapz(y_values, x_values, initial=0)
    return item.xdata, indefinite_integral.tolist(), False


def get_fourier(self, item):
    """Perform Fourier transformation on all selected data"""
    x_values = numpy.array(item.xdata)
    y_values = numpy.array(item.ydata)
    y_fourier = numpy.fft.fft(y_values)
    x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
    y_fourier = [value.real for value in y_fourier]
    return x_fourier, y_fourier, False


def get_inverse_fourier(self, item):
    """Perform Inverse Fourier transformation on all selected data"""
    x_values = numpy.array(item.xdata)
    y_values = numpy.array(item.ydata)
    y_fourier = numpy.fft.ifft(y_values)
    x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
    y_fourier = [value.real for value in y_fourier]
    return x_fourier, y_fourier, False


def transform(self, item, input_x, input_y):
    xdata, ydata = calculation.operation(
        item.xdata, item.ydata, input_x, input_y)
    return xdata, ydata, True


def combine(self):
    """Combine the selected data into a new data set"""
    keys = utilities.get_selected_keys(self)
    new_xdata = []
    new_ydata = []
    for key in keys:
        item = get_item(self, key)[0]
        new_xdata.extend(item.xdata)
        new_ydata.extend(item.ydata)

    # Create the sample itself
    new_xdata, new_ydata = sort_data(new_xdata, new_ydata)
    new_item = Data(self, new_xdata, new_ydata)
    new_item.filename = "Combined Data"
    new_item.color = plotting_tools.get_next_color(self)
    graphs.add_item(self, new_item)
    graphs.reset_clipboard(self)
