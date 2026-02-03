# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data transformations."""
import logging
import re
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs import misc, scales, utilities
from graphs.item import DataItem, EquationItem

import numexpr

import numpy

import scipy

import sympy


def perform_operation(window: Graphs.Window, name: str) -> None:
    """Perform an operation."""
    application = window.get_application()
    interaction_mode = window.get_mode()
    if name == "cut" and interaction_mode != 2:
        return
    args = []
    actions_settings = application.get_settings_child("actions")
    if name in ("center", "smoothen"):
        args = [actions_settings.get_enum(name)]
    if name == "smoothen":
        args.append(actions_settings.get_child(name))
    elif "translate" in name or "multiply" in name:
        operations = window.get_operations()
        try:
            args += [
                Graphs.evaluate_string(
                    operations.get_property(name + "_entry").get_text(),
                ),
            ]
        except ValueError as error:
            window.add_toast_string(str(error))
            return

    data = window.get_data()
    figure_settings = data.get_figure_settings()
    old_limits = figure_settings.get_limits()

    if hasattr(CommonOperations, name):
        all_success = getattr(CommonOperations, name)(window)
    else:
        all_success = False
        for item in data:
            if not item.get_selected():
                continue
            if isinstance(item, EquationItem):
                operations_class = EquationOperations
            elif isinstance(item, DataItem):
                operations_class = DataOperations
            else:
                continue
            success, message = operations_class.execute(
                item,
                name,
                figure_settings,
                interaction_mode,
                *args,
            )
            if message:
                window.add_toast_string(message)
            all_success = success or all_success
    if all_success:
        data.optimize_limits()
        data.add_history_state(old_limits)


class DataHelper():
    """Helper methods that assist with the handling of the data."""

    @staticmethod
    def get_xydata(
        interaction_mode: int,
        selected_limits: tuple[float, float],
        item: DataItem,
    ) -> tuple[list[float], list[float]]:
        """Get the X and Y data of a DataItem."""
        xdata, ydata = item.props.data
        if interaction_mode == 2:
            startx, stopx = selected_limits
            # If startx and stopx are not out of range, that is,
            # if the item data is within the highlight
            xmin = min(xdata)
            if not (startx < xmin and stopx < xmin or (startx > max(xdata))):
                xdata, ydata = DataHelper.filter_data(
                    xdata, ydata, ">=", startx,
                )
                xdata, ydata = DataHelper.filter_data(
                    xdata, ydata, "<=", stopx,
                )
            else:
                xdata = None
                ydata = None
        return xdata, ydata

    @staticmethod
    def get_selected_limits(
        figure_settings: Graphs.FigureSettings,
        interaction_mode: int,
        item: DataItem,
    ) -> tuple[float, float]:
        """Get the min and max value of the item within the selected range."""
        if item.get_xposition() == 0:
            min_bottom = figure_settings.get_min_bottom()
            max_bottom = figure_settings.get_max_bottom()
            if interaction_mode == 2:
                scale = figure_settings.get_bottom_scale()
                min_x = utilities.get_value_at_fraction(
                    figure_settings.get_min_selected(),
                    min_bottom,
                    max_bottom,
                    scale,
                )
                max_x = utilities.get_value_at_fraction(
                    figure_settings.get_max_selected(),
                    min_bottom,
                    max_bottom,
                    scale,
                )
            else:
                min_x, max_x = min_bottom, max_bottom
        else:
            min_top = figure_settings.get_min_top()
            max_top = figure_settings.get_max_top()
            if interaction_mode == 2:
                scale = figure_settings.get_top_scale()
                min_x = utilities.get_value_at_fraction(
                    figure_settings.get_min_selected(),
                    min_top,
                    max_top,
                    scale,
                )
                max_x = utilities.get_value_at_fraction(
                    figure_settings.get_max_selected(),
                    min_top,
                    max_top,
                    scale,
                )
            else:
                min_x, max_x = min_top, max_top
        return min_x, max_x

    @staticmethod
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

    @staticmethod
    def create_data_mask(
        xdata1: list,
        ydata1: list,
        xdata2: list,
        ydata2: list,
    ) -> bool:
        """
        Create a mask for matching pairs of coordinates.

        Returns:
        - Boolean mask indicating where pairs of coordinates match.
        """
        xdata1, ydata1, xdata2, ydata2 = \
            map(numpy.array, [xdata1, ydata1, xdata2, ydata2])
        return numpy.any((xdata1[:, None] == xdata2)
                         & (ydata1[:, None] == ydata2),
                         axis=1)

    @staticmethod
    def sort_data(xdata: list, ydata: list) -> (list, list):
        """Sort data."""
        return map(
            list,
            zip(
                *sorted(
                    zip(xdata, ydata),
                    key=lambda x_values: x_values[0],
                ),
            ),
        )

    @staticmethod
    def filter_range(xdata, ydata, prev_xdata, prev_ydata):
        """Filter range."""
        if min(xdata) >= min(prev_xdata) and max(xdata) <= max(prev_ydata):
            new_xdata, new_ydata = DataHelper.filter_data(
                prev_xdata, prev_ydata, ">=", min(xdata),
            )
            new_xdata, new_ydata = DataHelper.filter_data(
                new_xdata, new_ydata, "<=", max(xdata),
            )
            return new_xdata, new_ydata
        return xdata, ydata


class CommonOperations():
    """Operations to be performed on all kind of items."""

    @staticmethod
    def custom_transformation(window: Graphs.Window) -> bool:
        """Perform a custom operation on the dataset."""

        def on_accept(_dialog, input_x, input_y, discard):
            data = window.get_data()
            figure_settings = data.get_figure_settings()
            interaction_mode = window.get_canvas().get_mode()
            old_limits = figure_settings.get_limits()

            for item in data:
                if not item.get_selected():
                    continue
                if isinstance(item, EquationItem):
                    operations_class = EquationOperations
                elif isinstance(item, DataItem):
                    operations_class = DataOperations
                success, message = operations_class.execute(
                    item,
                    "transform",
                    figure_settings,
                    interaction_mode,
                    input_x,
                    input_y,
                    discard,
                )
                if message:
                    fail_message = _(
                        "Unable to perform transformation, "
                        "make sure the syntax is correct",
                    )
                    toast = message if success else fail_message
                    window.add_toast_string(toast)

                data.optimize_limits()
                data.add_history_state(old_limits)

        dialog = Graphs.TransformDialog.new(window)
        dialog.connect("accept", on_accept)
        return False

    @staticmethod
    def combine(window: Graphs.Window) -> bool:
        """Combine the selected data into a new data set."""
        data = window.get_data()
        new_xdata, new_ydata = [], []
        interaction_mode = window.get_mode()
        for item in data:
            if not item.get_selected():
                continue
            xdata, ydata = [], []
            selected_limits = DataHelper.get_selected_limits(
                data.get_figure_settings(),
                interaction_mode,
                item,
            )
            if isinstance(item, EquationItem):
                xdata, ydata = \
                    utilities.equation_to_data(item._equation, selected_limits)
            elif isinstance(item, DataItem):
                xdata, ydata = DataHelper().get_xydata(
                    interaction_mode, selected_limits, item,
                )
            else:
                continue
            if xdata is not None and ydata is not None:
                new_xdata.extend(xdata)
                new_ydata.extend(ydata)

        if (not new_xdata) or (not new_ydata):
            window.add_toast_string(
                _("No data found within the highlighted area"),
            )
            return False

        # Create the item itself
        new_xdata, new_ydata = DataHelper.sort_data(new_xdata, new_ydata)
        data.add_items([
            DataItem.new(
                data.get_selected_style_params(),
                new_xdata,
                new_ydata,
                name=_("Combined Data"),
            ),
        ])
        return True

    @staticmethod
    def shift(window: Graphs.Window) -> None:
        """Shift data."""
        interaction_mode = window.get_mode()
        data = window.get_data()
        figure_settings = data.get_figure_settings()
        data_list = ([
            item for item in data if item.get_selected()
            and isinstance(item, (EquationItem, DataItem))
        ])
        ranges = [
            figure_settings.get_max_left() - figure_settings.get_min_left(),
            figure_settings.get_max_right() - figure_settings.get_min_right(),
        ]
        left_scale = scales.Scale(figure_settings.get_left_scale())
        right_scale = scales.Scale(figure_settings.get_right_scale())
        for index, item in enumerate(data_list):
            selected_limits = DataHelper.get_selected_limits(
                figure_settings,
                interaction_mode,
                item,
            )
            scale = right_scale if item.get_yposition() else left_scale
            if isinstance(item, EquationItem):
                xdata, ydata = utilities.equation_to_data(
                    item.props.equation, selected_limits,
                )
            elif isinstance(item, DataItem):
                xdata, ydata = DataHelper().get_xydata(
                    interaction_mode, selected_limits, item,
                )
            if (not xdata) or (not ydata):
                continue

            shift_value = 0

            item_ = data_list[0]
            for i in range(index + 1):
                previous_item = item_
                item_ = data_list[i]
                y_range = ranges[item_.get_yposition()]

                if isinstance(previous_item, EquationItem):
                    prev_xdata, prev_ydata = utilities.equation_to_data(
                        previous_item.props.equation, selected_limits,
                    )
                else:
                    prev_xdata, prev_ydata = previous_item.props.data

                new_ydata = DataHelper.filter_range(
                    xdata,
                    ydata,
                    prev_xdata,
                    prev_ydata,
                )[1]
                ymin = min(x for x in new_ydata if x != 0)
                ymax = max(x for x in new_ydata if x != 0)

                if scale == scales.Scale.LOG:
                    shift_value += \
                        numpy.log10(abs(ymax / ymin)) \
                        + 0.1 * numpy.log10(y_range)
                elif scale == scales.Scale.LOG2:
                    shift_value += \
                        numpy.log2(abs(ymax / ymin)) \
                        + 0.1 * numpy.log2(y_range)
                else:
                    shift_value += (ymax - ymin) + 0.1 * y_range
            if shift_value == 0:
                continue
            shift_value = utilities.sig_fig_round(shift_value, 3)
            if isinstance(item, EquationItem):
                if scale == scales.Scale.LOG:
                    equation = f"({item.props.equation})*10**{shift_value}"
                elif scale == scales.Scale.LOG2:
                    equation = f"({item.props.equation})*2**{shift_value}"
                else:
                    equation = f"{item.equation}+{shift_value}"
                equation = utilities.preprocess(equation)
                equation = str(sympy.simplify(equation))
                item.props.equation = utilities.prettify_equation(equation)
                continue
            if isinstance(item, DataItem):
                if scale == scales.Scale.LOG:
                    new_ydata = [value * 10**shift_value for value in ydata]
                elif scale == scales.Scale.LOG2:
                    new_ydata = [value * 2**shift_value for value in ydata]
                else:  # Apply linear scaling
                    new_ydata = [value + shift_value for value in ydata]
                i = 0
                item_xdata, item_ydata = item.props.data
                for index, masked in enumerate(DataHelper.create_data_mask(
                    item_xdata, item_ydata, xdata, ydata,
                )):
                    # Change coordinates that were within span
                    if masked:
                        item_xdata[index] = xdata[i]
                        item_ydata[index] = new_ydata[i]
                        i += 1
                item.props.data = item_xdata, item_ydata
                continue
        return True


class EquationOperations():
    """Operations to be performed on equation items."""

    @staticmethod
    def execute(
        item: EquationItem,
        name: str,
        figure_settings: Graphs.FigureSettings,
        _interaction_mode: int,
        *args,
    ) -> tuple[bool, str]:
        """Execute the operation on the given item."""
        old_limits = figure_settings.get_limits()
        try:
            callback = getattr(EquationOperations, name)
            if name in ("normalize", "center", "transform"):
                args = [(
                    old_limits[item.get_xposition()],
                    old_limits[item.get_yposition() + 1],
                )] + list(args)
            equation = utilities.preprocess(str(callback(item, *args)))
            valid_equation = utilities.validate_equation(equation)
            if not valid_equation:
                raise misc.InvalidEquationError(
                    _(
                        "The operation on {name} "
                        "did not result in a plottable equation",
                    ).format(name=item.props.name),
                )
            equation = str(sympy.simplify(equation))
            item.props.equation = utilities.prettify_equation(equation)
        except misc.InvalidEquationError as error:
            return False, error.message
        except (NotImplementedError, AttributeError, KeyError):
            return False, _("Operation not supported for equations.")
        return True, ""

    @staticmethod
    def translate_x(item, offset) -> str:
        """Translate all selected data on the x-axis."""
        return re.sub(r"(?<!e)x(?!p)", f"(x+{offset})", item.equation)

    @staticmethod
    def translate_y(item, offset) -> str:
        """Translate all selected data on the y-axis."""
        return f"({item.equation})+{offset}"

    @staticmethod
    def multiply_x(item, multiplier: float) -> str:
        """Multiply all selected data on the x-axis."""
        return re.sub(r"(?<!e)x(?!p)", f"(x*{multiplier})", item.equation)

    @staticmethod
    def multiply_y(item, multiplier: float) -> str:
        """Multiply all selected data on the y-axis."""
        return f"({item.equation})*{multiplier}"

    @staticmethod
    def normalize(item, limits) -> str:
        """Normalize all selected data."""
        ydata = utilities.equation_to_data(item._equation, limits)[1]
        return f"({item.equation})/{max(ydata)}"

    @staticmethod
    def center(item, limits, center_maximum: int) -> str:
        """
        Center all selected data.

        Depending on the key, will center either on the middle coordinate, or
        on the maximum value of the data
        """
        xdata, ydata = utilities.equation_to_data(item._equation, limits)
        if center_maximum == 0:  # Center at maximum Y
            x = sympy.symbols("x")
            equation = sympy.sympify(utilities.preprocess(item._equation))
            derivative = sympy.diff(equation, x)
            critical_points = sympy.solveset(
                derivative,
                x,
                domain=sympy.Interval(limits[0], limits[1]),
            )
            endpoints = \
                [equation.subs(x, limits[0]), equation.subs(x, limits[1])]

            try:
                critical_values = \
                    [equation.subs(x, cp) for cp in critical_points]
                if critical_values:
                    max_index = critical_values.index(max(critical_values))
                    middle_value = list(critical_points)[max_index]
                else:
                    max_index = endpoints.index(max(endpoints))
                    middle_value = [limits[0], limits[1]][max_index]

            # If we don't manage to solve this analytically, just find
            # the maximum by calculating
            except TypeError:
                middle_index = ydata.index(max(ydata))
                middle_value = xdata[middle_index]

        elif center_maximum == 1:  # Center at middle
            middle_value = (min(xdata) + max(xdata)) / 2
        return re.sub(r"(?<!e)x(?!p)", f"(x+{middle_value})", item.equation)

    @staticmethod
    def derivative(item) -> str:
        """Calculate derivative of all selected data."""
        x = sympy.symbols("x")
        equation = utilities.preprocess(item._equation)
        return str(sympy.diff(equation, x))

    @staticmethod
    def integral(item) -> str:
        """Calculate indefinite integral of all selected data."""
        x = sympy.symbols("x")
        equation = utilities.preprocess(item._equation)
        return str(sympy.integrate(equation, x))

    @staticmethod
    def fft(item) -> str:
        """Perform Fourier transformation on all selected data."""
        x, k = sympy.symbols("x k")
        equation = utilities.preprocess(item._equation)
        equation = str(sympy.fourier_transform(equation, x, k))
        return equation.replace("k", "x")

    @staticmethod
    def inverse_fft(item) -> str:
        """Perform Inverse Fourier transformation on all selected data."""
        x, k = sympy.symbols("x k")
        equation = utilities.preprocess(item._equation)
        equation = str(sympy.fourier_transform(equation, x, k))
        return equation.replace("k", "x")

    @staticmethod
    def transform(
        item,
        limits: list,
        input_x: str,
        input_y: str,
        _discard: bool,
    ) -> str:
        """Perform custom transformation."""
        xdata, ydata = utilities.equation_to_data(item._equation, limits)
        local_dict = {
            "x": xdata,
            "y": ydata,
            "x_min": min(xdata),
            "x_max": max(xdata),
            "y_min": min(ydata),
            "y_max": max(ydata),
            "counts": len(xdata),
            "x_mean": numpy.mean(xdata),
            "y_mean": numpy.mean(ydata),
            "x_std": numpy.std(xdata),
            "y_std": numpy.std(ydata),
            "x_median": numpy.median(xdata),
            "y_median": numpy.median(ydata),
            "x_sum": sum(xdata),
            "y_sum": sum(ydata),
        }

        for key, value in local_dict.items():
            if key not in ("x", "y"):
                input_x = input_x.lower().replace(key, str(value))
                input_y = input_y.lower().replace(key, str(value))

        equation = re.sub(r"(?<!e)x(?!p)", input_x, item.equation)
        return input_y.lower().replace("y", equation)


_return = (list[float], list[float], bool, bool)


class DataOperations():
    """Operations to be performed on data items."""

    @staticmethod
    def execute(
        item: DataItem,
        name: str,
        figure_settings: Graphs.FigureSettings,
        interaction_mode: int,
        *args,
    ) -> tuple[bool, str]:
        """Execute the operation on the given item."""
        selected_limits = DataHelper.get_selected_limits(
            figure_settings,
            interaction_mode,
            item,
        )
        xdata, ydata = DataHelper.get_xydata(
            interaction_mode, selected_limits, item,
        )
        try:
            callback = getattr(DataOperations, name)
            if not (xdata is not None and len(xdata) != 0):
                return False, _("No data found within the highlighted area")
            message = ""
            new_xdata, new_ydata, sort, discard = callback(
                item, xdata, ydata, *args,
            )
        except NotImplementedError:
            return False, _("Operation not supported for data items")
        # May run into this exception for custom transformations:
        except (RuntimeError, ValueError, KeyError, SyntaxError) as exception:
            message = _("{name}: Error performing the operation")
            return False, message.format(name=exception.__class__.__name__)
        new_xdata, new_ydata = list(new_xdata), list(new_ydata)
        if discard and interaction_mode == 2:
            logging.debug("Discard is true")
            message = _(
                "Data that was outside of the highlighted area has"
                " been discarded",
            )
        else:
            logging.debug("Discard is false")
            mask = DataHelper.create_data_mask(
                item.get_xdata(),
                item.get_ydata(),
                xdata,
                ydata,
            )

            xdata, ydata = new_xdata, new_ydata
            new_xdata, new_ydata = item.props.data
            if xdata == []:  # If cut action was performed
                remove_list = \
                    [index for index, masked in enumerate(mask) if masked]
                for index in sorted(remove_list, reverse=True):
                    new_xdata.pop(index)
                    new_ydata.pop(index)
            else:
                i = 0
                for index, masked in enumerate(mask):
                    # Change coordinates that were within span
                    if masked:
                        new_xdata[index] = xdata[i]
                        new_ydata[index] = ydata[i]
                        i += 1

        if sort:
            logging.debug("Sorting data")
            new_xdata, new_ydata = DataHelper.sort_data(new_xdata, new_ydata)

        item.props.data = new_xdata, new_ydata
        return True, message

    @staticmethod
    def translate_x(_item, xdata: list, ydata: list, offset: float) -> _return:
        """
        Translate all selected data on the x-axis.

        Amount to be shifted is equal to the value in the translate_x entry
        widget.
        Will show a toast if a ValueError is raised, typically when a user
        entered an invalid number (e.g. comma instead of point separators)
        """
        return [value + offset for value in xdata], ydata, True, False

    @staticmethod
    def translate_y(_item, xdata: list, ydata: list, offset: float) -> _return:
        """
        Translate all selected data on the y-axis.

        Amount to be shifted is equal to the value in the translate_y entry
        widget.
        Will show a toast if a ValueError is raised, typically when a user
        entered an invalid number (e.g. comma instead of point separators)
        """
        return xdata, [value + offset for value in ydata], False, False

    @staticmethod
    def multiply_x(
        _item,
        xdata: list,
        ydata: list,
        multiplier: float,
    ) -> _return:
        """
        Multiply all selected data on the x-axis.

        Amount to be multiplied is equal to the value in the multiply_x entry
        widget
        Will show a toast if a ValueError is raised, typically when a user
        entered an invalid number (e.g. comma instead of point separators)
        """
        return [value * multiplier for value in xdata], ydata, True, False

    @staticmethod
    def multiply_y(
        _item,
        xdata: list,
        ydata: list,
        multiplier: float,
    ) -> _return:
        """
        Multiply all selected data on the y-axis.

        Amount to be multiplied is equal to the value in the multiply_y entry
        widget
        Will show a toast if a ValueError is raised, typically when a user
        entered an invalid number (e.g. comma instead of point separators)
        """
        return xdata, [value * multiplier for value in ydata], False, False

    @staticmethod
    def normalize(_item, xdata: list, ydata: list) -> _return:
        """Normalize all selected data."""
        return xdata, [value / max(ydata) for value in ydata], False, False

    @staticmethod
    def smoothen(
        _item,
        xdata: list,
        ydata: list,
        smooth_type: int,
        settings: Gio.Settings,
    ) -> _return:
        """Smoothen y-data."""
        if smooth_type == 0:
            minimum = settings.get_int("savgol-polynomial") + 1
            window_percentage = settings.get_int("savgol-window") / 100
            window = max(minimum, int(len(xdata) * window_percentage))
            new_ydata = scipy.signal.savgol_filter(
                ydata,
                window,
                settings.get_int("savgol-polynomial"),
            )
        elif smooth_type == 1:
            box_points = settings.get_int("moving-average-box")
            box = numpy.ones(box_points) / box_points
            new_ydata = numpy.convolve(ydata, box, mode="same")
        return xdata, new_ydata, False, False

    @staticmethod
    def center(
        _item,
        xdata: list,
        ydata: list,
        center_maximum: int,
    ) -> _return:
        """
        Center all selected data.

        Depending on the key, will center either on the middle coordinate, or
        on the maximum value of the data
        """
        if center_maximum == 0:  # Center at maximum Y
            middle_index = ydata.index(max(ydata))
            middle_value = xdata[middle_index]
        elif center_maximum == 1:  # Center at middle
            middle_value = (min(xdata) + max(xdata)) / 2
        new_xdata = [coordinate - middle_value for coordinate in xdata]
        return new_xdata, ydata, True, False

    @staticmethod
    def cut(_item, _xdata, _ydata) -> _return:
        """Cut selected data over the span that is selected."""
        return [], [], False, False

    @staticmethod
    def derivative(_item, xdata: list, ydata: list) -> _return:
        """Calculate derivative of all selected data."""
        x_values = numpy.array(xdata)
        y_values = numpy.array(ydata)
        dy_dx = numpy.gradient(y_values, x_values)
        return xdata, dy_dx.tolist(), False, True

    @staticmethod
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

    @staticmethod
    def fft(_item, xdata: list, ydata: list) -> _return:
        """Perform Fourier transformation on all selected data."""
        x_values = numpy.array(xdata)
        y_values = numpy.array(ydata)
        y_fourier = numpy.fft.fft(y_values)
        x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
        y_fourier = [value.real for value in y_fourier]
        return x_fourier, y_fourier, False, True

    @staticmethod
    def inverse_fft(_item, xdata: list, ydata: list) -> _return:
        """Perform Inverse Fourier transformation on all selected data."""
        x_values = numpy.array(xdata)
        y_values = numpy.array(ydata)
        y_fourier = numpy.fft.ifft(y_values)
        x_fourier = numpy.fft.fftfreq(len(x_values), x_values[1] - x_values[0])
        y_fourier = [value.real for value in y_fourier]
        return x_fourier, y_fourier, False, True

    @staticmethod
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
            "counts": len(xdata),
            "x_mean": numpy.mean(xdata),
            "y_mean": numpy.mean(ydata),
            "x_std": numpy.std(xdata),
            "y_std": numpy.std(ydata),
            "x_median": numpy.median(xdata),
            "y_median": numpy.median(ydata),
            "x_sum": sum(xdata),
            "y_sum": sum(ydata),
        }
        # Add array of zeros to return values, such that output remains a list
        # of the correct size, even when a float is given as input.
        return (
            numexpr.evaluate(
                utilities.preprocess(input_x) + "+ 0*x",
                local_dict,
            ),
            numexpr.evaluate(
                utilities.preprocess(input_y) + "+ 0*y",
                local_dict,
            ),
            True,
            discard,
        )
