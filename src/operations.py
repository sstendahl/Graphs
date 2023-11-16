# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import logging
from gettext import gettext as _

from graphs import utilities
from graphs.item import DataItem

import numexpr

import numpy

import scipy


def get_data(self, item):
    """
    Retrieve item from datadict with start and stop index.
    If interaction_mode is set to "SELECT"
    """
    xdata = item.props.xdata
    ydata = item.props.ydata
    new_xdata = xdata.copy()
    new_ydata = ydata.copy()
    start_index = 0
    stop_index = len(xdata)
    if self.get_mode() == 2:
        figure_settings = self.get_data().get_figure_settings()
        if item.get_xposition() == 0:
            xmin = figure_settings.get_min_bottom()
            xmax = figure_settings.get_max_bottom()
            scale = figure_settings.get_bottom_scale()
        else:
            xmin = figure_settings.get_min_top()
            xmax = figure_settings.get_max_top()
            scale = figure_settings.get_top_scale()
        startx = utilities.get_value_at_fraction(
            figure_settings.get_min_selected(), xmin, xmax, scale,
        )
        stopx = utilities.get_value_at_fraction(
            figure_settings.get_max_selected(), xmin, xmax, scale,
        )

        # If startx and stopx are not out of range, that is,
        # if the item data is within the highlight
        if not ((startx < min(xdata) and stopx < min(xdata)) or (
                startx > max(xdata))):
            new_x, new_y = sort_data(xdata, ydata)
            numpy_x = numpy.asarray(new_x)
            with contextlib.suppress(IndexError):
                start_index = numpy.where(numpy_x > startx)[0][0]
                stop_index = numpy.where(numpy_x > stopx)[0][0]
            new_xdata = new_x[start_index:stop_index]
            new_ydata = new_y[start_index:stop_index]
        else:
            new_xdata = None
            new_ydata = None
            start_index = None
            stop_index = None
    return new_xdata, new_ydata, start_index, stop_index


def sort_data(xdata, ydata):
    return map(list, zip(*sorted(
        zip(xdata, ydata), key=lambda x_values: x_values[0],
    )))


def perform_operation(self, callback, *args):
    data_selected = False
    data = self.get_data()
    old_limits = data.get_figure_settings().get_limits()
    for item in data:
        if not (item.get_selected() and isinstance(item, DataItem)):
            continue
        xdata, ydata, start_index, stop_index = get_data(self, item)
        if xdata is not None and len(xdata) != 0:
            data_selected = True
            new_xdata, new_ydata, sort, discard = callback(
                item, xdata, ydata, *args)
            if discard:
                logging.debug("Discard is true")
                item.props.xdata = new_xdata
                item.props.ydata = new_ydata
            else:
                logging.debug("Discard is false")
                item.props.xdata[start_index:stop_index] = new_xdata
                item.props.ydata[start_index:stop_index] = new_ydata
            if sort:
                logging.debug("Sorting data")
                item.xdata, item.ydata = sort_data(item.xdata, item.ydata)
        item.notify("xdata")
        item.notify("ydata")
    if not data_selected:
        self.get_window().add_toast_string(
            _("No data found within the highlighted area"))
        return
    data.optimize_limits()
    data.add_history_state(old_limits)


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
    return xdata, [value / max(ydata) for value in ydata], False, False


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


def shift(item, xdata, ydata, left_scale, right_scale, items, ranges):
    """
    Shifts data vertically with respect to each other
    By default it scales linear data by 1.2 times the total span of the
    ydata, and log data 10 to the power of the yspan.
    """
    data_list = [
        item for item in items
        if item.get_selected() and isinstance(item, DataItem)
    ]

    y_range = ranges[1] if item.get_yposition() else ranges[0]

    shift_value_log = 0
    shift_value_linear = 0

    for index, item_ in enumerate(data_list):
        # Compare first element with itself, not "previous" item
        index = 1 if index == 0 and len(data_list) > 1 else index

        previous_item = data_list[index - 1]

        # Only use selected span when obtaining values to determine shift value
        full_xdata = numpy.asarray(data_list[index].props.xdata)
        start = 0
        stop = len(data_list[index].ydata)
        with contextlib.suppress(IndexError):
            start = numpy.where(full_xdata >= xdata[0])[0][0]
            stop = numpy.where(full_xdata >= xdata[-1])[0][0]

        ymin = min(x for x in previous_item.ydata[start:stop] if x != 0)
        ymax = max(x for x in previous_item.ydata[start:stop] if x != 0)
        scale = right_scale if item.get_yposition() else left_scale
        if scale == 1:  # Use log values for log scaling
            shift_value_log += \
                numpy.log10(abs(ymax / ymin)) + 0.1 * numpy.log10(y_range)
        else:
            shift_value_linear += (ymax - ymin) + 0.1 * y_range
        if item.get_uuid() == item_.get_uuid():
            if scale == 1:  # Log scaling
                new_ydata = [value * 10 ** shift_value_log for value in ydata]
            else:
                new_ydata = [value + shift_value_linear for value in ydata]
            return xdata, new_ydata, False, False
    return xdata, ydata, False, False


def cut(_item, _xdata, _ydata):
    """Cut selected data over the span that is selected"""
    return [], [], False, False


def derivative(_item, xdata, ydata):
    """Calculate derivative of all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    dy_dx = numpy.gradient(y_values, x_values)
    return xdata, dy_dx.tolist(), False, True


def integral(_item, xdata, ydata):
    """Calculate indefinite integral of all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    indefinite_integral = \
        scipy.integrate.cumtrapz(y_values, x_values, initial=0).tolist()
    return xdata, indefinite_integral, False, True


def fft(_item, xdata, ydata):
    """Perform Fourier transformation on all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    y_fourier = numpy.fft.fft(y_values)
    x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
    y_fourier = [value.real for value in y_fourier]
    return x_fourier, y_fourier, False, True


def inverse_fft(_item, xdata, ydata):
    """Perform Inverse Fourier transformation on all selected data"""
    x_values = numpy.array(xdata)
    y_values = numpy.array(ydata)
    y_fourier = numpy.fft.ifft(y_values)
    x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
    y_fourier = [value.real for value in y_fourier]
    return x_fourier, y_fourier, False, True


def transform(_item, xdata, ydata, input_x, input_y, discard=False):
    local_dict = {
        "x": xdata, "y": ydata,
        "x_min": min(xdata), "x_max": max(xdata),
        "y_min": min(ydata), "y_max": max(ydata),
    }
    # Add array of zeros to return values, such that output remains a list
    # of the correct size, even when a float is given as input.
    return (
        numexpr.evaluate(utilities.preprocess(input_x) + "+ 0*x", local_dict),
        numexpr.evaluate(utilities.preprocess(input_y) + "+ 0*y", local_dict),
        True, discard,
    )


def combine(self):
    """Combine the selected data into a new data set"""
    new_xdata, new_ydata = [], []
    for item in self.get_data():
        if not (item.get_selected() and isinstance(item, DataItem)):
            continue
        xdata, ydata = get_data(self, item)[:2]
        new_xdata.extend(xdata)
        new_ydata.extend(ydata)

    # Create the item itself
    new_xdata, new_ydata = sort_data(new_xdata, new_ydata)
    style = self.get_figure_style_manager().get_selected_style_params()
    self.get_data().add_items(
        [DataItem.new(style, new_xdata, new_ydata, name=_("Combined Data"))],
    )
