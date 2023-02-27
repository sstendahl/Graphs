# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from graphs import calculation, plotting_tools, utilities
from graphs import clipboard, graphs, operation_tools
from graphs.data import Data
from graphs.misc import InteractionMode

import numpy

from scipy import integrate


def operation(self, callback, *args):
    try:
        keys = utilities.get_selected_keys(self)
        # Select data being selected via select mode
        if self.interaction_mode == InteractionMode.SELECT:
            start_stop = operation_tools.select_data(self, keys)
        else:
            # If mode isn't selection, set start and stop
            start_stop = {}
            for key in keys:
                item = self.datadict[key]
                start_stop[key] = [0, len(item.xdata)]
        for key in keys:
            item = operation_tools.get_item(self, key)
            xdata, ydata, sort = callback(self, item, *args)
            start_index, stop_index = start_stop[key][0], start_stop[key][1]
            self.datadict[key].xdata[start_index:stop_index] = xdata
            self.datadict[key].ydata[start_index:stop_index] = ydata
            if sort:
                operation_tools.sort_data(
                    self.datadict[key].xdata, self.datadict[key].ydata)
        operation_tools.delete_selected(self)
        clipboard.add(self)
        plotting_tools.refresh_plot(self)
    except Exception:
        message = "Couldn't perform operation"
        self.main_window.add_toast(message)
        logging.exception(message)
        operation_tools.delete_selected(self)


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
    return calculation.operation(
        item.xdata, item.ydata, input_x, input_y), True


def combine(self):
    """Combine the selected data into a new data set"""
    keys = utilities.get_selected_keys(self)
    if self.interaction_mode == InteractionMode.SELECT:
        operation_tools.select_data(self, keys)
    new_xdata = []
    new_ydata = []
    for key in keys:
        item = operation_tools.get_item(self, key)
        new_xdata.extend(item.xdata)
        new_ydata.extend(item.ydata)

    # Create the sample itself
    new_xdata, new_ydata = operation_tools.sort_data(new_xdata, new_ydata)
    new_item = Data(self, new_xdata, new_ydata)
    new_item.filename = "Combined Data"
    filename_list = utilities.get_all_filenames(self)

    if new_item.filename in filename_list:
        new_item.filename = graphs.get_duplicate_filename(
            self, new_item.filename)
    color = plotting_tools.get_next_color(self)
    self.datadict[new_item.key] = new_item
    graphs.reset_clipboard(self)
    graphs.add_sample_to_menu(self, new_item.filename, color, new_item.key)
    operation_tools.delete_selected(self)
    graphs.select_item(self, new_item.key)
    plotting_tools.refresh_plot(self)
