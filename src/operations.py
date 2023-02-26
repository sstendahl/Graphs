# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from graphs import clipboard, graphs, operation_tools
from graphs import plotting_tools, utilities
from graphs.data import Data
from graphs.misc import InteractionMode

import numpy

from scipy import integrate


def operation(self, callback):
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
        callback(self, keys, start_stop)
        operation_tools.delete_selected(self)
        clipboard.add(self)
        plotting_tools.refresh_plot(self)
    except Exception:
        message = "Couldn't perform operation"
        self.main_window.add_toast(message)
        logging.exception(message)
        operation_tools.delete_selected(self)


def get_item(self, key):
    if f"{key}_selected" in self.datadict:
        return self.datadict[f"{key}_selected"]
    if self.interaction_mode != InteractionMode.SELECT:
        return self.datadict[key]
    return None


def translate_x(self, keys, start_stop):
    """
    Translate all selected data on the x-axis
    Amount to be shifted is equal to the value in the translate_x entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    win = self.main_window
    try:
        offset = eval(win.translate_x_entry.get_text())
    except Exception as exception:
        exception_type = exception.__class__.__name__
        message = f"{exception_type}: Unable to do translation, \
make sure to enter a valid number"
        win.add_toast(message)
        logging.exception(message)
        offset = 0
    for key in keys:
        item = get_item(self, key)
        new_xdata = [value + offset for value in item.xdata]
        start_index, stop_index = start_stop[key][0], start_stop[key][1]
        self.datadict[key].xdata[start_index:stop_index] = new_xdata
        self.datadict[key].xdata, self.datadict[key].ydata = \
            operation_tools.sort_data(
            self.datadict[key].xdata, self.datadict[key].ydata)


def translate_y(self, keys, start_stop):
    """
    Translate all selected data on the y-axis
    Amount to be shifted is equal to the value in the translate_y entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    win = self.main_window
    try:
        offset = eval(win.translate_y_entry.get_text())
    except Exception as exception:
        exception_type = exception.__class__.__name__
        message = f"{exception_type}: Unable to do translation, \
make sure to enter a valid number"
        win.add_toast(message)
        logging.exception(message)
        offset = 0
    for key in keys:
        item = get_item(self, key)
        new_ydata = [value + offset for value in item.ydata]
        start_index, stop_index = start_stop[key][0], start_stop[key][1]
        self.datadict[key].ydata[start_index:stop_index] = new_ydata


def multiply_x(self, keys, start_stop):
    """
    Multiply all selected data on the x-axis
    Amount to be shifted is equal to the value in the multiply_x entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    win = self.main_window
    try:
        multiplier = eval(win.multiply_x_entry.get_text())
    except Exception as exception:
        exception_type = exception.__class__.__name__
        message = f"{exception_type}: Unable to do multiplication, \
make sure to enter a valid number"
        win.add_toast(message)
        logging.exception(message)
        multiplier = 1
    for key in keys:
        item = get_item(self, key)
        new_xdata = [value * multiplier for value in item.xdata]
        start_index, stop_index = start_stop[key][0], start_stop[key][1]
        self.datadict[key].xdata[start_index:stop_index] = new_xdata
        self.datadict[key].xdata, self.datadict[key].ydata = \
            operation_tools.sort_data(
            self.datadict[key].xdata, self.datadict[key].ydata)


def multiply_y(self, keys, start_stop):
    """
    Multiply all selected data on the y-axis
    Amount to be shifted is equal to the value in the multiply_y entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    win = self.main_window
    try:
        multiplier = eval(win.multiply_y_entry.get_text())
    except Exception as exception:
        exception_type = exception.__class__.__name__
        message = f"{exception_type}: Unable to do multiplication, \
make sure to enter a valid number"
        win.add_toast(message)
        logging.exception(message)
        multiplier = 1
    for key in keys:
        item = get_item(self, key)
        new_ydata = [value * multiplier for value in item.ydata]
        start_index, stop_index = start_stop[key][0], start_stop[key][1]
        self.datadict[key].ydata[start_index:stop_index] = new_ydata


def normalize(self, keys, start_stop):
    """Normalize all selected data"""
    for key in keys:
        item = get_item(self, key)
        new_ydata = [value / max(item.ydata) for value in item.ydata]
        start_index, stop_index = start_stop[key][0], start_stop[key][1]
        self.datadict[key].ydata[start_index:stop_index] = new_ydata
        self.datadict[key].xdata[start_index:stop_index] = item.xdata


def smoothen(self, keys, start_stop):
    """Smoothen y-data."""
    for key in keys:
        item = get_item(self, key)
        box_points = 4
        box = numpy.ones(box_points) / box_points
        new_ydata = numpy.convolve(item.ydata, box, mode="same")
        start_index, stop_index = start_stop[key][0], start_stop[key][1]
        self.datadict[key].ydata[start_index:stop_index] = new_ydata


def center(self, keys, start_stop):
    """
    Center all selected data
    Depending on the key, will center either on the middle coordinate, or on
    the maximum value of the data
    """
    for key in keys:
        item = get_item(self, key)
        if self.preferences.config[
                "action_center_data"] == "Center at maximum Y value":
            middle_index = item.ydata.index(max(item.ydata))
            middle_value = item.xdata[middle_index]
            new_xdata = \
                [coordinate - middle_value for coordinate in item.xdata]
        elif self.preferences.config[
                "action_center_data"] == "Center at middle coordinate":
            middle_value = (min(item.xdata) + max(item.xdata)) / 2
            new_xdata = \
                [coordinate - middle_value for coordinate in item.xdata]
        start_index, stop_index = start_stop[key][0], start_stop[key][1]
        self.datadict[key].ydata[start_index:stop_index] = item.ydata
        self.datadict[key].xdata[start_index:stop_index] = new_xdata
        self.datadict[key].xdata, self.datadict[key].ydata = \
            operation_tools.sort_data(
            self.datadict[key].xdata, self.datadict[key].ydata)


def shift_vertically(self, keys, start_stop):
    """
    Shifts data vertically with respect to each other
    By default it scales linear data by 1.5 times the total span of the
    ydata, and log data by a factor of 10000.
    """
    shift_value_log = 1
    shift_value_linear = 0
    for key in keys:
        item = get_item(self, key)
        ymin = min(x for x in item.ydata if x != 0)
        ymax = max(x for x in item.ydata if x != 0)
        shift_value_linear += 1.2 * (ymax - ymin)
        shift_value_log *= 10 ** (numpy.log10(ymax / ymin))
        if item.plot_y_position == "left":
            if self.plot_settings.yscale == "log":
                item.ydata = [value * shift_value_log for value in item.ydata]
            if self.plot_settings.yscale == "linear":
                item.ydata = \
                    [value + shift_value_linear for value in item.ydata]
        if item.plot_y_position == "right":
            if self.plot_settings.right_scale == "log":
                item.ydata = [value * shift_value_log for value in item.ydata]
            if self.plot_settings.right_scale == "linear":
                item.ydata = \
                    [value + shift_value_linear for value in item.ydata]
        if f"{key}_selected" in self.datadict:
            start_index, stop_index = start_stop[key][0], start_stop[key][1]
            self.datadict[key].ydata[start_index:stop_index] = item.ydata


def combine(self, keys, start_stop):
    """Combine the selected data into a new data set"""
    new_xdata = []
    new_ydata = []
    for key in keys:
        item = get_item(self, key)
        new_xdata.extend(item.xdata.copy())
        new_ydata.extend(item.ydata.copy())

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


def cut_selected(self, keys, start_stop):
    """Cut selected data over the span that is selected"""
    if self.interaction_mode == InteractionMode.SELECT:
        for key in keys:
            # If our item is among the selected samples, we will cut those
            if f"{key}_selected" in self.datadict:
                # Create empty arrays that will be equal to the new cut data
                new_x = []
                new_y = []
                selected_item = self.datadict[f"{key}_selected"]
                if selected_item is None:
                    continue
                for _index, (x_value, y_value) in enumerate(zip(
                        self.datadict[key].xdata,
                        self.datadict[key].ydata)):
                    # Appends the values that are within the selected span
                    xdata = selected_item.xdata
                    if x_value < min(xdata) or x_value > max(xdata):
                        new_x.append(x_value)
                        new_y.append(y_value)
                self.datadict[key].xdata = new_x
                self.datadict[key].ydata = new_y


def get_derivative(self, keys, start_stop):
    """Calculate derivative of all selected data"""
    for key in keys:
        item = get_item(self, key)
        x_values = numpy.array(item.xdata)
        y_values = numpy.array(item.ydata)
        dy_dx = numpy.gradient(y_values, x_values)
        self.datadict[key].xdata = item.xdata
        self.datadict[key].ydata = dy_dx.tolist()


def get_integral(self, keys, start_stop):
    """Calculate indefinite integral of all selected data"""
    for key in keys:
        item = get_item(self, key)
        x_values = numpy.array(item.xdata)
        y_values = numpy.array(item.ydata)
        indefinite_integral = integrate.cumtrapz(y_values, x_values, initial=0)
        self.datadict[key].xdata = item.xdata
        self.datadict[key].ydata = indefinite_integral.tolist()


def get_fourier(self, keys, start_stop):
    """Perform Fourier transformation on all selected data"""
    for key in keys:
        item = get_item(self, key)
        x_values = numpy.array(item.xdata)
        y_values = numpy.array(item.ydata)
        y_fourier = numpy.fft.fft(y_values)
        x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
        y_fourier = [value.real for value in y_fourier]
        self.datadict[key].ydata = y_fourier
        self.datadict[key].xdata = x_fourier


def get_inverse_fourier(self, keys, start_stop):
    """Perform Inverse Fourier transformation on all selected data"""
    for key in keys:
        item = get_item(self, key)
        x_values = numpy.array(item.xdata)
        y_values = numpy.array(item.ydata)
        y_fourier = numpy.fft.ifft(y_values)
        x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
        y_fourier = [value.real for value in y_fourier]
        self.datadict[key].ydata = y_fourier
        self.datadict[key].xdata = x_fourier
