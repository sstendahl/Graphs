# SPDX-License-Identifier: GPL-3.0-or-later
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
    new_xdata = item.props.xdata
    new_ydata = item.props.ydata

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
        if not ((startx < min(new_xdata) and stopx < min(new_xdata)) or (
                startx > max(new_xdata))):
            new_xdata, new_ydata = \
                filter_data(new_xdata, new_ydata, ">=", startx)
            new_xdata, new_ydata = \
                filter_data(new_xdata, new_ydata, "<=", stopx)
        else:
            new_xdata = None
            new_ydata = None
    return new_xdata, new_ydata


def filter_data(xdata, ydata, condition, value):
    """Filter coordinates based on the given condition."""
    xdata = numpy.array(xdata)
    ydata = numpy.array(ydata)

    conditions = {
        "<=": numpy.less_equal,
        ">=": numpy.greater_equal,
        "==": numpy.equal,
    }

    mask = conditions[condition](xdata, value)

    xdata_filtered = xdata[mask]
    ydata_filtered = ydata[mask]

    return list(xdata_filtered), list(ydata_filtered)


def create_data_mask(xdata1, ydata1, xdata2, ydata2):
    """
    Create a mask for matching pairs of coordinates.

    Returns:
    - Boolean mask indicating where pairs of coordinates match.
    """
    xdata1, ydata1, xdata2, ydata2 = \
        map(numpy.array, [xdata1, ydata1, xdata2, ydata2])
    return numpy.any(
        (xdata1[:, None] == xdata2) & (ydata1[:, None] == ydata2), axis=1)


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
        xdata, ydata = get_data(self, item)
        if xdata is not None and len(xdata) != 0:
            data_selected = True
            new_xdata, new_ydata, sort, discard = callback(
                item, xdata, ydata, *args)
            new_xdata, new_ydata = list(new_xdata), list(new_ydata)
            if discard:
                logging.debug("Discard is true")
                self.get_window().add_toast_string(
                    _("Data that was outside of the highlighted area has been"
                      " discarded"))
                item.props.xdata = new_xdata
                item.props.ydata = new_ydata
            else:
                logging.debug("Discard is false")
                mask = create_data_mask(item.props.xdata,
                                        item.props.ydata,
                                        xdata,
                                        ydata,
                                        )

                if new_xdata == []:  # If cut action was performed
                    remove_list = \
                        [index for index, masked in enumerate(mask) if masked]
                    for index in sorted(remove_list, reverse=True):
                        item.props.xdata.pop(index)
                        item.props.ydata.pop(index)
                else:
                    i = 0
                    for index, masked in enumerate(mask):
                        # Change coordinates that were within span
                        if masked:
                            item.props.xdata[index] = new_xdata[i]
                            item.props.ydata[index] = new_ydata[i]
                            i += 1
            if sort:
                logging.debug("Sorting data")
                item.xdata, item.ydata = sort_data(item.xdata, item.ydata)
        item.notify("xdata")
        item.notify("ydata")
        canvas = self.get_window().get_canvas()
        canvas.highlight.extents = (0, 0)
        canvas.set_property("min_selected", 0)
        canvas.set_property("max_selected", 0)
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


def smoothen(_item, xdata, ydata, smooth_type, params):
    """Smoothen y-data."""
    if smooth_type == 0:
        minimum = params["savgol-polynomial"] + 1
        window_percentage = params["savgol-window"] / 100
        window = max(minimum, int(len(xdata) * window_percentage))
        new_ydata = scipy.signal.savgol_filter(ydata,
                                               window,
                                               params["savgol-polynomial"])
    elif smooth_type == 1:
        box_points = params["moving-average-box"]
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
        new_xdata, new_ydata = xdata, ydata
        if (min(xdata) >= min(previous_item.xdata)
                and max(xdata) <= max(previous_item.xdata)):
            new_xdata, new_ydata = filter_data(
                previous_item.xdata, previous_item.ydata, ">=", min(xdata))
            new_xdata, new_ydata = filter_data(
                new_xdata, new_ydata, "<=", max(xdata))

        ymin = min(x for x in new_ydata if x != 0)
        ymax = max(x for x in new_ydata if x != 0)

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
