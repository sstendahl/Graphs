# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from graphs import calculation, utilities
from graphs.item import Item

import numpy

import scipy


def get_data(self, item):
    """
    Retrieve item from datadict with start and stop index.
    If interaction_mode is set to "SELECT"
    """
    xdata = item.xdata
    ydata = item.ydata
    new_xdata = xdata.copy()
    new_ydata = ydata.copy()
    start_index = 0
    stop_index = len(xdata)
    if self.props.mode == 2:
        canvas = self.props.main_window.toast_overlay.get_child()
        startx, stopx = canvas.highlight.get_start_stop(
            item.xposition == 0)

        # If startx and stopx are not out of range, that is,
        # if the item data is within the highlight
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


def perform_operation(self, callback, *args):
    data_selected = False
    for item in self.props.data.props.items:
        if not item.selected or item.props.item_type != "Item":
            continue
        xdata, ydata, start_index, stop_index = get_data(self, item)
        if xdata is not None and len(xdata) != 0:
            data_selected = True
            new_xdata, new_ydata, sort, discard = callback(
                item, xdata, ydata, *args)
            if discard:
                logging.debug("Discard is true")
                item.xdata = new_xdata
                item.ydata = new_ydata
            else:
                logging.debug("Discard is false")
                item.xdata[start_index:stop_index] = new_xdata
                item.ydata[start_index:stop_index] = new_ydata
            if sort:
                logging.debug("Sorting data")
                sorted_x, sorted_y = sort_data(item.xdata, item.ydata)
                item.xdata = sorted_x
                item.ydata = sorted_y
    if not data_selected:
        self.main_window.add_toast(
            _("No data found within the highlighted area"))
    utilities.optimize_limits(self)
    self.props.clipboard.add()


def translate_x(_item, xdata, ydata, offset):
    """
    Translate all selected data on the x-axis
    Amount to be shifted is equal to the value in the translate_x entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return [value + offset for value in xdata], ydata, True, False


def translate_y(_item, xdata, ydata, offset):
    """
    Translate all selected data on the y-axis
    Amount to be shifted is equal to the value in the translate_y entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return xdata, [value + offset for value in ydata], False, False


def multiply_x(_item, xdata, ydata, multiplier):
    """
    Multiply all selected data on the x-axis
    Amount to be shifted is equal to the value in the multiply_x entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return [value * multiplier for value in xdata], ydata, True, False


def multiply_y(_item, xdata, ydata, multiplier):
    """
    Multiply all selected data on the y-axis
    Amount to be shifted is equal to the value in the multiply_y entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    return xdata, [value * multiplier for value in ydata], False, False


def normalize(_item, xdata, ydata):
    """Normalize all selected data"""
    new_ydata = [value / max(ydata) for value in ydata]
    return xdata, new_ydata, False, False


def smoothen(_item, xdata, ydata):
    """Smoothen y-data."""
    box_points = 4
    box = numpy.ones(box_points) / box_points
    new_ydata = numpy.convolve(ydata, box, mode="same")
    return xdata, new_ydata, False, False


def center(_item, xdata, ydata, center_maximum):
    """
    Center all selected data
    Depending on the key, will center either on the middle coordinate, or on
    the maximum value of the data
    """
    if center_maximum == 0:  # Center at maximum Y
        middle_index = ydata.index(max(ydata))
        middle_value = xdata[middle_index]
    elif center_maximum == 1:  # Center at middle
        middle_value = (min(xdata) + max(xdata)) / 2
    new_xdata = [coordinate - middle_value for coordinate in xdata]
    return new_xdata, ydata, True, False


def shift_vertically(item, xdata, ydata, left_scale, right_scale, items):
    """
    Shifts data vertically with respect to each other
    By default it scales linear data by 1.2 times the total span of the
    ydata, and log data 10 to the power of the yspan.
    """
    shift_value_log = 1
    shift_value_linear = 0
    data_list = [item for item in items
                 if item.selected and item.props.item_type == "Item"]

    for index, data_item in enumerate(data_list):
        previous_ydata = data_list[index - 1].ydata
        ymin = min(x for x in previous_ydata if x != 0)
        ymax = max(x for x in previous_ydata if x != 0)
        if item.yposition == "left":
            linear = (left_scale == "linear")
        if item.yposition == "right":
            linear = (right_scale == "linear")
        if linear:
            shift_value_linear += 1.2 * (ymax - ymin)
        else:
            shift_value_log += numpy.log10(ymax / ymin)
        if item.key == data_item.key:
            if linear:
                new_ydata = [value + shift_value_linear for value in ydata]
            else:
                new_ydata = [value * 10 ** shift_value_log for value in ydata]
            return xdata, new_ydata, False, False


def cut_selected(_item, _xdata, _ydata):
    """Cut selected data over the span that is selected"""
    return [], [], False, False


def get_derivative(_item, xdata, ydata):
    """Calculate derivative of all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    dy_dx = numpy.gradient(y_values, x_values)
    return xdata, dy_dx.tolist(), False, True


def get_integral(_item, xdata, ydata):
    """Calculate indefinite integral of all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    indefinite_integral = \
        scipy.integrate.cumtrapz(y_values, x_values, initial=0).tolist()
    return xdata, indefinite_integral, False, True


def get_fourier(_item, xdata, ydata):
    """Perform Fourier transformation on all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    y_fourier = numpy.fft.fft(y_values)
    x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
    y_fourier = [value.real for value in y_fourier]
    return x_fourier, y_fourier, False, True


def get_inverse_fourier(_item, xdata, ydata):
    """Perform Inverse Fourier transformation on all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    y_fourier = numpy.fft.ifft(y_values)
    x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
    y_fourier = [value.real for value in y_fourier]
    return x_fourier, y_fourier, False, True


def transform(_item, xdata, ydata, input_x, input_y, discard=False):
    new_xdata, new_ydata = calculation.operation(
        xdata, ydata, input_x, input_y)
    return new_xdata, new_ydata, True, discard


def combine(self):
    """Combine the selected data into a new data set"""
    new_xdata, new_ydata = [], []
    for item in self.props.data.props.items:
        if not item.selected or item.props.item_type != "Item":
            continue
        xdata, ydata = get_data(self, item)[:2]
        new_xdata.extend(xdata)
        new_ydata.extend(ydata)

    # Create the item itself
    new_xdata, new_ydata = sort_data(new_xdata, new_ydata)
    self.props.data.add_items(
        [Item.new(self, new_xdata, new_ydata, name=_("Combined Data"))],
    )
