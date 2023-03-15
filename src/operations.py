# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from graphs import calculation, clipboard, graphs, plotting_tools, utilities
from graphs.data import Data
from graphs.misc import InteractionMode

import numpy

from scipy import integrate


def get_data(self, item):
    """
    Retrieve item from datadict with start and stop index.
    If interaction_mode is set to "SELECT"
    """
    xdata = item.xdata
    ydata = item.ydata
    start_index = 0
    stop_index = len(xdata)
    if self.interaction_mode == InteractionMode.SELECT:
        startx, stopx = self.canvas.highlight.get_start_stop(
            item.plot_x_position == "bottom")

        # If startx and stopx are not out of range, that is,
        # if the sample data is within the highlight
        if not ((startx < min(xdata) and stopx < min(xdata)) or (
                startx > max(xdata))):
            new_x, new_y = sort_data(xdata, ydata)
            found_start = False
            found_stop = False
            for index, value in enumerate(xdata):
                if value > startx and not found_start:
                    start_index = index
                    found_start = True
                if value > stopx and not found_stop:
                    stop_index = index
                    found_stop = True
            new_xdata = new_x[start_index:stop_index]
            new_ydata = new_y[start_index:stop_index]
        else:
            new_xdata = None
            new_ydata = None
            start_index = None
            stop_index = None
    return new_xdata, new_ydata, start_index, stop_index


def sort_data(xdata, ydata):
    sorted_lists = sorted(
        zip(xdata, ydata), key=lambda x_values: x_values[0])
    sorted_x, sorted_y = zip(*sorted_lists)
    return list(sorted_x), list(sorted_y)


def operation(self, callback, *args):
    try:
        keys = utilities.get_selected_keys(self)
        clipboard.add(self)
        for key in keys:
            item = self.datadict[key]
            xdata, ydata, start_index, stop_index = get_data(self, item)
            if xdata is not None:
                new_xdata, new_ydata, sort, discard = callback(
                    self, item, xdata, ydata, *args)
                if discard:
                    logging.info("Discard is true")
                    item.xdata = new_xdata
                    item.ydata = new_ydata
                else:
                    logging.info("Discard is false")
                    item.xdata[start_index:stop_index] = new_xdata
                    item.ydata[start_index:stop_index] = new_ydata
                if sort:
                    logging.info("Sorting data")
                    sorted_x, sorted_y = sort_data(item.xdata, item.ydata)
                    item.xdata = sorted_x
                    item.ydata = sorted_y

        plotting_tools.refresh_plot(self)
    except Exception as exception:
        exception_type = exception.__class__.__name__
        message = f"Couldn't perform operation: {exception_type}"
        self.main_window.add_toast(message)
        logging.exception(message)


def translate_x(self, item, xdata, ydata, offset):
    """
    Translate all selected data on the x-axis
    Amount to be shifted is equal to the value in the translate_x entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return [value + offset for value in xdata], ydata, True, False


def translate_y(self, item, xdata, ydata, offset):
    """
    Translate all selected data on the y-axis
    Amount to be shifted is equal to the value in the translate_y entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return xdata, [value + offset for value in ydata], False, False


def multiply_x(self, item, xdata, ydata, multiplier):
    """
    Multiply all selected data on the x-axis
    Amount to be shifted is equal to the value in the multiply_x entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return [value * multiplier for value in xdata], ydata, True, False


def multiply_y(self, item, xdata, ydata, multiplier):
    """
    Multiply all selected data on the y-axis
    Amount to be shifted is equal to the value in the multiply_y entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return xdata, [value * multiplier for value in ydata], False, False


def normalize(self, item, xdata, ydata):
    """Normalize all selected data"""
    new_ydata = [value / max(ydata) for value in ydata]
    return xdata, new_ydata, False, False


def smoothen(self, item, xdata, ydata):
    """Smoothen y-data."""
    box_points = 4
    box = numpy.ones(box_points) / box_points
    new_ydata = numpy.convolve(ydata, box, mode="same")
    return xdata, new_ydata, False, False


def center(self, item, xdata, ydata):
    """
    Center all selected data
    Depending on the key, will center either on the middle coordinate, or on
    the maximum value of the data
    """
    if self.preferences.config["action_center_data"] == \
            "Center at maximum Y value":
        middle_index = ydata.index(max(ydata))
        middle_value = xdata[middle_index]
    elif self.preferences.config["action_center_data"] == \
            "Center at middle coordinate":
        middle_value = (min(xdata) + max(xdata)) / 2
    new_xdata = [coordinate - middle_value for coordinate in xdata]
    return new_xdata, ydata, False, False


def shift_vertically(self, item, xdata, ydata,
                     shift_value_log=1, shift_value_linear=0):
    """
    Shifts data vertically with respect to each other
    By default it scales linear data by 1.5 times the total span of the
    ydata, and log data by a factor of 10000.
    """
    ymin = min(x for x in ydata if x != 0)
    ymax = max(x for x in ydata if x != 0)
    shift_value_linear += 1.2 * (ymax - ymin)
    shift_value_log *= 10 ** (numpy.log10(ymax / ymin))
    if item.plot_y_position == "left":
        if self.plot_settings.yscale == "log":
            new_ydata = [value * shift_value_log for value in ydata]
        if self.plot_settings.yscale == "linear":
            new_ydata = [value + shift_value_linear for value in ydata]
    if item.plot_y_position == "right":
        if self.plot_settings.right_scale == "log":
            new_ydata = [value * shift_value_log for value in ydata]
        if self.plot_settings.right_scale == "linear":
            new_ydata = [value + shift_value_linear for value in ydata]
    return xdata, new_ydata, False, False


def cut_selected(self, item, xdata, ydata):
    """Cut selected data over the span that is selected"""
    return [], [], False, False


def get_derivative(self, item, xdata, ydata):
    """Calculate derivative of all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    dy_dx = numpy.gradient(y_values, x_values)
    return xdata, dy_dx.tolist(), False, True


def get_integral(self, item, xdata, ydata):
    """Calculate indefinite integral of all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    indefinite_integral = integrate.cumtrapz(y_values, x_values, initial=0)
    return xdata, indefinite_integral.tolist(), False, True


def get_fourier(self, item, xdata, ydata):
    """Perform Fourier transformation on all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    y_fourier = numpy.fft.fft(y_values)
    x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
    y_fourier = [value.real for value in y_fourier]
    return x_fourier, y_fourier, False, True


def get_inverse_fourier(self, item, xdata, ydata):
    """Perform Inverse Fourier transformation on all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    y_fourier = numpy.fft.ifft(y_values)
    x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
    y_fourier = [value.real for value in y_fourier]
    return x_fourier, y_fourier, False, True


def transform(self, item, xdata, ydata, input_x, input_y, discard=False):
    new_xdata, new_ydata = calculation.operation(
        xdata, ydata, input_x, input_y)
    return new_xdata, new_ydata, True, discard


def combine(self):
    """Combine the selected data into a new data set"""
    keys = utilities.get_selected_keys(self)
    new_xdata = []
    new_ydata = []
    for key in keys:
        xdata, ydata = get_data(self, self.datadict[key])[0:1]
        new_xdata.extend(xdata)
        new_ydata.extend(ydata)

    # Create the sample itself
    new_xdata, new_ydata = sort_data(new_xdata, new_ydata)
    new_item = Data(self, new_xdata, new_ydata)
    new_item.filename = "Combined Data"
    new_item.color = plotting_tools.get_next_color(self)
    graphs.add_item(self, new_item)
    clipboard.reset(self)
