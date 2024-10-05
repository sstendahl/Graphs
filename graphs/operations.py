# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data transformations."""
import logging
import sys
from gettext import gettext as _

from gi.repository import Graphs

from graphs import misc, utilities
from graphs.item import DataItem, EquationItem

import numexpr

import numpy

import scipy

import sympy


def get_data(window: Graphs.Window, item: DataItem):
    """
    Retrieve item from datadict with start and stop index.

    If interaction_mode is set to "SELECT"
    """
    new_xdata = item.props.xdata
    new_ydata = item.props.ydata

    canvas = window.get_canvas()
    if canvas.get_mode() == 2:
        figure_settings = window.get_data().get_figure_settings()
        if item.get_xposition() == 0:
            xmin = figure_settings.get_min_bottom()
            xmax = figure_settings.get_max_bottom()
            scale = figure_settings.get_bottom_scale()
        else:
            xmin = figure_settings.get_min_top()
            xmax = figure_settings.get_max_top()
            scale = figure_settings.get_top_scale()
        startx = utilities.get_value_at_fraction(
            figure_settings.get_min_selected(),
            xmin,
            xmax,
            scale,
        )
        stopx = utilities.get_value_at_fraction(
            figure_settings.get_max_selected(),
            xmin,
            xmax,
            scale,
        )
        # If startx and stopx are not out of range, that is,
        # if the item data is within the highlight
        new_min = min(new_xdata)
        a = startx < new_min and stopx < new_min
        if not (a or (startx > max(new_xdata))):
            new_xdata, new_ydata = filter_data(
                new_xdata, new_ydata, ">=", startx,
            )
            new_xdata, new_ydata = filter_data(
                new_xdata, new_ydata, "<=", stopx,
            )
        else:
            new_xdata = None
            new_ydata = None
    return new_xdata, new_ydata


def filter_data(
    xdata: list,
    ydata: list,
    condition: str,
    value: float,
) -> list:
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


def create_data_mask(xdata1: list, ydata1: list, xdata2: list, ydata2: list):
    """
    Create a mask for matching pairs of coordinates.

    Returns:
    - Boolean mask indicating where pairs of coordinates match.
    """
    xdata1, ydata1, xdata2, ydata2 = \
        map(numpy.array, [xdata1, ydata1, xdata2, ydata2])
    return numpy.any((xdata1[:, None] == xdata2) & (ydata1[:, None] == ydata2),
                     axis=1)


def sort_data(xdata: list, ydata: list) -> (list, list):
    """Sort data."""
    return map(
        list,
        zip(*sorted(
            zip(xdata, ydata),
            key=lambda x_values: x_values[0],
        )),
    )


def perform_operation(
    application: Graphs.Application, window: Graphs.Window, name: str
) -> None:
    """Perform an operation."""
    if name in ("combine", ):
        return getattr(this, name)(window)
    elif name == "custom_transformation":

        def on_accept(_dialog, input_x, input_y, discard):
            try:
                _apply(window, transform, input_x, input_y, discard)
            except (RuntimeError, KeyError) as exception:
                toast = _(
                    "{name}: Unable to do transformation, \
make sure the syntax is correct",
                ).format(name=exception.__class__.__name__)
                window.add_toast_string(toast)
                logging.exception(_("Unable to do transformation"))

        dialog = Graphs.TransformDialog.new(window)
        dialog.connect("accept", on_accept)
        return
    elif name == "cut" and window.get_canvas().get_mode() != 2:
        return
    args = []
    actions_settings = application.get_settings_child("actions")
    if name in ("center", "smoothen"):
        args = [actions_settings.get_enum(name)]
    if name == "smoothen":
        params = {}
        settings = actions_settings.get_child("smoothen")
        for setting in settings:
            params[setting] = int(settings.get_int(setting))
        args += [params]
    elif name == "shift":
        figure_settings = window.get_data().get_figure_settings()
        right_range = (
            figure_settings.get_max_right() - figure_settings.get_min_right()
        )
        left_range = (
            figure_settings.get_max_left() - figure_settings.get_min_left()
        )
        args += [
            figure_settings.get_left_scale(),
            figure_settings.get_right_scale(),
            window.get_data().get_items(),
            [left_range, right_range],
        ]
    elif "translate" in name or "multiply" in name:
        try:
            args += [
                utilities.string_to_float(
                    window.get_property(name + "_entry").get_text(),
                ),
            ]
        except ValueError as error:
            window.add_toast_string(str(error))
            return
#  operation_class = ItemOperations
    operation_class = EquationOperations
    _apply(window, getattr(operation_class, name), *args)

# _apply(window, getattr(operation_class, name), *args)


def _apply(window, callback, *args):
    data = window.get_data()
    figure_settings = data.get_figure_settings()
    data_selected = False
    old_limits = figure_settings.get_limits()
    for item in data:
        operation_item = isinstance(item, (DataItem, EquationItem))
        if not (item.get_selected() and operation_item):
            continue
        if isinstance(item, EquationItem):
            callback(item, *args)
            if not callback:
                window.add_toast_string(
                    _(
                        f"Could not perform operation on {item.name}, "
                        + "this operation is not supported for equations.",
                    ),
                )
        elif isinstance(item, DataItem):
            _apply_data(window, item, figure_settings, data_selected)

    data.optimize_limits()
    data.add_history_state_with_limits(old_limits)


def _apply_data(window, item, figure_settings, data_selected):
    xdata, ydata = get_data(window, item)
    if xdata is not None and len(xdata) != 0:
        data_selected = True
        new_xdata, new_ydata, sort, discard = callback(
            item, xdata, ydata, *args,
        )
        new_xdata, new_ydata = list(new_xdata), list(new_ydata)
        canvas = window.get_canvas()
        if discard and canvas.get_mode() == 2:
            logging.debug("Discard is true")
            window.add_toast_string(
                _(
                    "Data that was outside of the highlighted area has"
                    " been discarded",
                ),
            )
            item.props.xdata = new_xdata
            item.props.ydata = new_ydata
        else:
            logging.debug("Discard is false")
            mask = create_data_mask(
                item.props.xdata,
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
    figure_settings.set_selection_range(0, 0)
    if not data_selected:
        window.add_toast_string(_("No data found within the highlighted area"))
    return


_return = (list[float], list[float], bool, bool)


class EquationOperations():

    def translate_x(_item, offset) -> _return:
        """
        Translate all selected data on the x-axis.

        Amount to be shifted is equal to the value in the translate_x entry widget
        Will show a toast if a ValueError is raised, typically when a user entered
        an invalid number (e.g. comma instead of point separators)
        """

        x = sympy.symbols("x")
        # TODO: MAKE SURE INSTANCES WITH AN X (LIKE EXP(X)) ARE NOT REPLACED
        equation = _item.equation.replace("x", f"(x+{offset})")
        equation = sympy.sympify(utilities.preprocess(equation))
        _item.equation = str(sympy.simplify(equation))
        return True

    def translate_y(_item, offset) -> _return:
        """
        Translate all selected data on the y-axis.

        Amount to be shifted is equal to the value in the translate_y entry widget
        Will show a toast if a ValueError is raised, typically when a user entered
        an invalid number (e.g. comma instead of point separators)
        """
        equation = f"({_item.equation})+{offset}"
        equation = sympy.sympify(utilities.preprocess(equation))
        _item.equation = str(sympy.simplify(equation))
        return True

    def multiply_x(_item, multiplier: float) -> _return:
        """
        Multiply all selected data on the x-axis.

        Amount to be shifted is equal to the value in the multiply_x entry widget
        Will show a toast if a ValueError is raised, typically when a user entered
        an invalid number (e.g. comma instead of point separators)
        """
        equation = _item.equation.replace("x", f"(x*{multiplier})")
        equation = sympy.sympify(utilities.preprocess(equation))
        _item.equation = str(sympy.simplify(equation))
        return True

    def multiply_y(_item, multiplier: float) -> _return:
        """
        Multiply all selected data on the y-axis.

        Amount to be shifted is equal to the value in the multiply_y entry widget
        Will show a toast if a ValueError is raised, typically when a user entered
        an invalid number (e.g. comma instead of point separators)
        """
        equation = f"({_item.equation})*{multiplier}"
        equation = sympy.sympify(utilities.preprocess(equation))
        _item.equation = str(sympy.simplify(equation))
        return True

    def normalize(_item) -> _return:
        """Normalize all selected data."""
        # TODO: FIX RANGE
        xdata, ydata = utilities.equation_to_data(item._equation, [0, 1])
        equation = f"({_item.equation})/{max(ydata)}"
        equation = sympy.sympify(utilities.preprocess(equation))
        _item.equation = str(sympy.simplify(equation))
        return True

    def smoothen(_item, ) -> None:
        """Smoothen y-data."""
        return False

    def center(_item, middle_value: int) -> _return:
        """
        Center all selected data.

        Depending on the key, will center either on the middle coordinate, or on
        the maximum value of the data
        """
        equation = _item.equation.replace("x", f"(x-{middle_value})")
        equation = sympy.sympify(utilities.preprocess(equation))
        _item.equation = str(sympy.simplify(equation))
        return

    def shift(
        item,
        left_scale: int,
        right_scale: int,
        items: misc.ItemList,
        ranges: tuple[float, float],
    ) -> _return:
        """
        Shifts data vertically with respect to each other.

        By default it scales linear data by 1.2 times the total span of the
        ydata, and log data 10 to the power of the yspan.
        """
        # TODO: THIS DOESN OT WORK AT ALL YET
        data_list = [item for item in items]

        y_range = ranges[1] if item.get_yposition() else ranges[0]

        shift_value_log = 0
        shift_value_linear = 0

        # TODO: FIX LIMITS HERE
        xdata, ydata = utilities.equation_to_data(item._equation, [0, 1])
        for index, item_ in enumerate(data_list):
            # Compare first element with itself, not "previous" item
            index = 1 if index == 0 and len(data_list) > 1 else index

            previous_item = data_list[index - 1]
            prev_xdata, prev_ydata = \
                utilities.equation_to_data(previous_item._equation, [0, 1])
            # Only use selected span when obtaining values to determine shift value
            new_xdata, new_ydata = xdata, ydata
            if (
                min(xdata) >= min(prev_xdata)
                and max(xdata) <= max(prev_ydata)
            ):
                new_xdata, new_ydata = filter_data(
                    prev_xdata, prev_ydata, ">=", min(xdata))
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
                    new_ydata = [
                        value * 10**shift_value_log for value in ydata
                    ]
                else:
                    new_ydata = [value + shift_value_linear for value in ydata]
            shift_value = shift_value_log if scale == 1 else shift_value_linear
            print(shift_value)
            item.equation = f"{item.equation}+{shift_value}"
        return True

    def cut(_item) -> _return:
        """Cut selected data over the span that is selected."""
        return False

    def derivative(_item) -> _return:
        """Calculate derivative of all selected data."""
        x = sympy.symbols("x")
        equation = utilities.preprocess(_item._equation)
        equation = sympy.diff(equation, x)
        _item.equation = str(equation)
        return True

    def integral(_item) -> _return:
        """Calculate indefinite integral of all selected data."""
        x = sympy.symbols("x")
        equation = utilities.preprocess(_item._equation)
        equation = sympy.integrate(equation, x)
        _item.equation = str(equation)
        return True

    def fft(_item) -> _return:
        """Perform Fourier transformation on all selected data."""
        x, k = sympy.symbols("x k")
        equation = utilities.preprocess(_item._equation)
        equation = str(sympy.fourier_transform(equation, x, k))
        equation = equation.replace("k", "x")
        _item._equation = equation
        return True

    def inverse_fft(_item) -> _return:
        """Perform Inverse Fourier transformation on all selected data."""
        x, k = sympy.symbols("x k")
        equation = utilities.preprocess(_item._equation)
        equation = str(sympy.fourier_transform(equation, x, k))
        equation = equation.replace("k", "x")
        _item._equation = equation
        return True

    def transform(
        _item,
        xdata: list,
        ydata: list,
        input_x: str,
        input_y: str,
        discard: bool = False,
    ) -> _return:
        """Perform custom transformation."""
        local_dict = {
            "x": xdata,
            "y": ydata,
            "x_min": min(xdata),
            "x_max": max(xdata),
            "y_min": min(ydata),
            "y_max": max(ydata),
        }
        # Add array of zeros to return values, such that output remains a list
        # of the correct size, even when a float is given as input.
        return (
            numexpr.evaluate(
                utilities.preprocess(input_x) + "+ 0*x", local_dict
            ),
            numexpr.evaluate(
                utilities.preprocess(input_y) + "+ 0*y", local_dict
            ),
            True,
            discard,
        )

    def combine(window: Graphs.Window) -> None:
        """Combine the selected data into a new data set."""
        new_xdata, new_ydata = [], []
        data = window.get_data()
        for item in data:
            if not (item.get_selected() and isinstance(item, DataItem)):
                continue
            xdata, ydata = get_data(window, item)[:2]
            new_xdata.extend(xdata)
            new_ydata.extend(ydata)

        # Create the item itself
        new_xdata, new_ydata = sort_data(new_xdata, new_ydata)
        data.add_items([
            DataItem.new(
                data.get_selected_style_params(),
                new_xdata,
                new_ydata,
                name=_("Combined Data"),
            ),
        ])


class ItemOperations():

    def translate_x(_item, xdata: list, ydata: list, offset: float) -> _return:
        """
        Translate all selected data on the x-axis.

        Amount to be shifted is equal to the value in the translate_x entry widget
        Will show a toast if a ValueError is raised, typically when a user entered
        an invalid number (e.g. comma instead of point separators)
        """
        return [value + offset for value in xdata], ydata, True, False

    def translate_y(_item, xdata: list, ydata: list, offset: float) -> _return:
        """
        Translate all selected data on the y-axis.

        Amount to be shifted is equal to the value in the translate_y entry widget
        Will show a toast if a ValueError is raised, typically when a user entered
        an invalid number (e.g. comma instead of point separators)
        """
        return xdata, [value + offset for value in ydata], False, False

    def multiply_x(
        _item, xdata: list, ydata: list, multiplier: float,
    ) -> _return:
        """
        Multiply all selected data on the x-axis.

        Amount to be shifted is equal to the value in the multiply_x entry widget
        Will show a toast if a ValueError is raised, typically when a user entered
        an invalid number (e.g. comma instead of point separators)
        """
        return [value * multiplier for value in xdata], ydata, True, False

    def multiply_y(
        _item, xdata: list, ydata: list, multiplier: float,
    ) -> _return:
        """
        Multiply all selected data on the y-axis.

        Amount to be shifted is equal to the value in the multiply_y entry widget
        Will show a toast if a ValueError is raised, typically when a user entered
        an invalid number (e.g. comma instead of point separators)
        """
        return xdata, [value * multiplier for value in ydata], False, False

    def normalize(_item, xdata: list, ydata: list) -> _return:
        """Normalize all selected data."""
        return xdata, [value / max(ydata) for value in ydata], False, False

    def smoothen(
        _item,
        xdata: list,
        ydata: list,
        smooth_type: int,
        params: dict,
    ) -> None:
        """Smoothen y-data."""
        if smooth_type == 0:
            minimum = params["savgol-polynomial"] + 1
            window_percentage = params["savgol-window"] / 100
            window = max(minimum, int(len(xdata) * window_percentage))
            new_ydata = scipy.signal.savgol_filter(
                ydata,
                window,
                params["savgol-polynomial"],
            )
        elif smooth_type == 1:
            box_points = params["moving-average-box"]
            box = numpy.ones(box_points) / box_points
            new_ydata = numpy.convolve(ydata, box, mode="same")
        return xdata, new_ydata, False, False

    def center(
        _item, xdata: list, ydata: list, center_maximum: int,
    ) -> _return:
        """
        Center all selected data.

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

    def shift(
        item,
        xdata: list,
        ydata: list,
        left_scale: int,
        right_scale: int,
        items: misc.ItemList,
        ranges: tuple[float, float],
    ) -> _return:
        """
        Shifts data vertically with respect to each other.

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
            if (
                min(xdata) >= min(previous_item.xdata)
                and max(xdata) <= max(previous_item.xdata)
            ):
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
                    new_ydata = [
                        value * 10**shift_value_log for value in ydata
                    ]
                else:
                    new_ydata = [value + shift_value_linear for value in ydata]
                return xdata, new_ydata, False, False
        return xdata, ydata, False, False

    def cut(_item, _xdata, _ydata) -> _return:
        """Cut selected data over the span that is selected."""
        return [], [], False, False

    def derivative(_item, xdata: list, ydata: list) -> _return:
        """Calculate derivative of all selected data."""
        x_values = numpy.array(xdata)
        y_values = numpy.array(ydata)
        dy_dx = numpy.gradient(y_values, x_values)
        return xdata, dy_dx.tolist(), False, True

    def integral(_item, xdata: list, ydata: list) -> _return:
        """Calculate indefinite integral of all selected data."""
        x_values = numpy.array(xdata)
        y_values = numpy.array(ydata)
        indefinite_integral = scipy.integrate.cumulative_trapezoid(
            y_values,
            x_values,
            initial=0,
        ).tolist()
        return xdata, indefinite_integral, False, True

    def fft(_item, xdata: list, ydata: list) -> _return:
        """Perform Fourier transformation on all selected data."""
        x_values = numpy.array(xdata)
        y_values = numpy.array(ydata)
        y_fourier = numpy.fft.fft(y_values)
        x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
        y_fourier = [value.real for value in y_fourier]
        return x_fourier, y_fourier, False, True

    def inverse_fft(_item, xdata: list, ydata: list) -> _return:
        """Perform Inverse Fourier transformation on all selected data."""
        x_values = numpy.array(xdata)
        y_values = numpy.array(ydata)
        y_fourier = numpy.fft.ifft(y_values)
        x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
        y_fourier = [value.real for value in y_fourier]
        return x_fourier, y_fourier, False, True

    def transform(_item) -> _return:
        """Perform custom transformation."""
        return False

    def combine(window: Graphs.Window) -> None:
        """Combine the selected data into a new data set."""
        return False
