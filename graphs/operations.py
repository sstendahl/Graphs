# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data transformations."""
import logging
import re
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs import misc, utilities
from graphs.item import DataItem

import numexpr

import numpy

import scipy

import sympy


def perform_operation(window: Graphs.Window, name: str) -> None:
    """Perform an operation."""
    interaction_mode = window.get_mode()
    if name == "cut" and interaction_mode != Graphs.Mode.SELECT:
        return
    args = []
    actions_settings = Graphs.Application.get_settings_child("actions")
    if name in ("center", "smoothen"):
        args = [actions_settings.get_enum(name)]
    if name == "smoothen":
        args.append(actions_settings.get_child(name))
    elif "translate" in name or "multiply" in name:
        args.append(window.get_operation_value(name))

    data = window.get_data()
    figure_settings = data.get_figure_settings()

    if hasattr(CommonOperations, name):
        all_success = getattr(CommonOperations, name)(window)
    else:
        all_success = False
        for item in data:
            if not item.get_selected():
                continue
            if isinstance(item, Graphs.EquationItem):
                operations_class = EquationOperations
            elif isinstance(item, Graphs.DataItem):
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
        data.add_history_state()
        data.optimize_limits()


class DataHelper():
    """Helper methods that assist with the handling of the data."""

    @staticmethod
    def get_xydata(
        interaction_mode: Graphs.Mode,
        selected_limits: tuple[float, float],
        item: Graphs.DataItem,
    ) -> tuple[numpy.ndarray, numpy.ndarray]:
        """Get the X and Y data of a DataItem."""
        xdata, ydata = item.get_xydata()
        if interaction_mode != Graphs.Mode.SELECT:
            return xdata, ydata
        startx, stopx = selected_limits
        # If startx and stopx are not out of range, that is,
        # if the item data is within the highlight
        xmin = min(xdata)
        if not (startx < xmin and stopx < xmin or (startx > max(xdata))):
            mask = numpy.greater_equal(xdata, startx)
            mask &= numpy.less_equal(xdata, stopx)

            return xdata[mask], ydata[mask]
        return None, None

    @staticmethod
    def get_selected_limits(
        figure_settings: Graphs.FigureSettings,
        interaction_mode: Graphs.Mode,
        item: Graphs.DataItem,
    ) -> tuple[float, float]:
        """Get the min and max value of the item within the selected range."""
        if item.get_xposition() == 0:
            min_bottom = figure_settings.get_min_bottom()
            max_bottom = figure_settings.get_max_bottom()
            if interaction_mode == Graphs.Mode.SELECT:
                scale = figure_settings.get_bottom_scale()
                min_x = Graphs.get_value_at_fraction(
                    figure_settings.get_min_selected(),
                    min_bottom,
                    max_bottom,
                    scale,
                )
                max_x = Graphs.get_value_at_fraction(
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
            if interaction_mode == Graphs.Mode.SELECT:
                scale = figure_settings.get_top_scale()
                min_x = Graphs.get_value_at_fraction(
                    figure_settings.get_min_selected(),
                    min_top,
                    max_top,
                    scale,
                )
                max_x = Graphs.get_value_at_fraction(
                    figure_settings.get_max_selected(),
                    min_top,
                    max_top,
                    scale,
                )
            else:
                min_x, max_x = min_top, max_top
        return min_x, max_x

    @staticmethod
    def create_data_mask(
        xdata1: numpy.ndarray,
        ydata1: numpy.ndarray,
        xdata2: numpy.ndarray,
        ydata2: numpy.ndarray,
    ) -> bool:
        """
        Create a mask for matching pairs of coordinates.

        Returns:
        - Boolean mask indicating where pairs of coordinates match.
        """
        return numpy.any((xdata1[:, None] == xdata2)
                         & (ydata1[:, None] == ydata2),
                         axis=1)

    @staticmethod
    def sort_data(xdata: list, ydata: list) -> (list, list):
        """Sort data."""
        return map(
            numpy.array,
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
            mask = numpy.greater_equal(xdata, min(xdata))
            mask &= numpy.less_equal(xdata, max(xdata))

            return xdata[mask], ydata[mask]
        return xdata, ydata


class CommonOperations():
    """Operations to be performed on all kind of items."""

    @staticmethod
    def custom_transformation(window: Graphs.Window) -> bool:
        """Perform a custom operation on the dataset."""

        def on_accept(_dialog, input_x, input_y, discard):
            data = window.get_data()
            figure_settings = data.get_figure_settings()

            for item in data:
                if not item.get_selected():
                    continue
                if isinstance(item, Graphs.EquationItem):
                    operations_class = EquationOperations
                elif isinstance(item, Graphs.DataItem):
                    operations_class = DataOperations
                success, message = operations_class.execute(
                    item,
                    "transform",
                    figure_settings,
                    window.get_mode(),
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

                data.add_history_state()
                data.optimize_limits()

        dialog = Graphs.TransformDialog.new(window)
        dialog.connect("accept", on_accept)
        return False

    @staticmethod
    def combine(window: Graphs.Window) -> bool:
        """Combine the selected data into a new data set."""
        data = window.get_data()
        mode = window.get_mode()
        settings = data.get_figure_settings()

        new_xdata, new_ydata, new_xerr, new_yerr = [], [], [], []
        some_x, some_y = False, False

        for item in data:
            if not item.get_selected():
                continue

            lims = DataHelper.get_selected_limits(settings, mode, item)
            xdata, ydata = None, None

            if isinstance(item, Graphs.EquationItem):
                eq = item.get_preprocessed_equation()
                xdata, ydata = utilities.equation_to_data(eq, lims)
                new_xerr, new_yerr = None, None
            elif isinstance(item, Graphs.DataItem):
                xdata, ydata = DataHelper().get_xydata(mode, lims, item)
                xerr = item.get_xerr()
                if xerr is not None and new_xerr is not None:
                    new_xerr.extend(xerr)
                    some_x = True
                else:
                    new_xerr = None
                yerr = item.get_yerr()
                if yerr is not None and new_xerr is not None:
                    new_yerr.extend(yerr)
                    some_y = True
                else:
                    new_xerr = None

            if xdata is not None and ydata is not None:
                new_xdata.extend(xdata)
                new_ydata.extend(ydata)

        if not new_xdata or not new_ydata:
            window.add_toast_string(_("No data found in highlighted area"))
            return False

        if (some_x and new_xerr is None) or (some_y and new_yerr is None):
            msg = _("Some items lack error bars; they will be discarded")
            window.add_toast_string(msg)

        new_xdata, new_ydata = DataHelper.sort_data(new_xdata, new_ydata)
        data.add_items([
            DataItem.new(
                data.get_selected_style_params(),
                new_xdata,
                new_ydata,
                xerr=new_xerr,
                yerr=new_yerr,
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
            and isinstance(item, (Graphs.EquationItem, Graphs.DataItem))
        ])
        ranges = [
            figure_settings.get_max_left() - figure_settings.get_min_left(),
            figure_settings.get_max_right() - figure_settings.get_min_right(),
        ]
        left_scale = figure_settings.get_left_scale()
        right_scale = figure_settings.get_right_scale()
        for index, item in enumerate(data_list):
            selected_limits = DataHelper.get_selected_limits(
                figure_settings,
                interaction_mode,
                item,
            )
            scale = right_scale if item.get_yposition() else left_scale
            if isinstance(item, Graphs.EquationItem):
                xdata, ydata = utilities.equation_to_data(
                    item.get_preprocessed_equation(),
                    selected_limits,
                )
            elif isinstance(item, Graphs.DataItem):
                xdata, ydata = DataHelper().get_xydata(
                    interaction_mode, selected_limits, item,
                )
            if min(xdata.size, ydata.size) == 0:
                continue

            shift_value = 0

            item = data_list[0]
            for i in range(index + 1):
                previous_item = item
                item = data_list[i]
                y_range = ranges[item.get_yposition()]

                if isinstance(previous_item, Graphs.EquationItem):
                    prev_xdata, prev_ydata = utilities.equation_to_data(
                        previous_item.get_preprocessed_equation(),
                        selected_limits,
                    )
                else:
                    prev_xdata, prev_ydata = previous_item.get_xydata()

                new_ydata = DataHelper.filter_range(
                    xdata,
                    ydata,
                    prev_xdata,
                    prev_ydata,
                )[1]
                ymin = min(x for x in new_ydata if x != 0)
                ymax = max(x for x in new_ydata if x != 0)

                if scale == Graphs.Scale.LOG:
                    shift_value += \
                        numpy.log10(abs(ymax / ymin)) \
                        + 0.1 * numpy.log10(y_range)
                elif scale == Graphs.Scale.LOG2:
                    shift_value += \
                        numpy.log2(abs(ymax / ymin)) \
                        + 0.1 * numpy.log2(y_range)
                else:
                    shift_value += (ymax - ymin) + 0.1 * y_range
            if shift_value == 0:
                continue
            shift_value = Graphs.math_tools_sig_fig_round(shift_value, 3)
            if isinstance(item, Graphs.EquationItem):
                equation = item.get_preprocessed_equation()
                if scale == Graphs.Scale.LOG:
                    equation = f"({equation})*10**{shift_value}"
                elif scale == Graphs.Scale.LOG2:
                    equation = f"({equation})*2**{shift_value}"
                else:
                    equation = f"{equation}+{shift_value}"
                equation = str(sympy.simplify(equation))
                item.set_equation(Graphs.prettify_equation(equation))
                continue
            if isinstance(item, Graphs.DataItem):
                if scale == Graphs.Scale.LOG:
                    new_ydata = [value * 10**shift_value for value in ydata]
                elif scale == Graphs.Scale.LOG2:
                    new_ydata = [value * 2**shift_value for value in ydata]
                else:  # Apply linear scaling
                    new_ydata = [value + shift_value for value in ydata]
                i = 0
                item_xdata, item_ydata = item.get_xydata()
                for index, masked in enumerate(DataHelper.create_data_mask(
                    item_xdata, item_ydata, xdata, ydata,
                )):
                    # Change coordinates that were within span
                    if masked:
                        item_xdata = item_xdata.copy()
                        item_ydata = item_ydata.copy()
                        item_xdata[index] = xdata[i]
                        item_ydata[index] = new_ydata[i]
                        i += 1
                item.set_xydata((item_xdata, item_ydata))
                continue
        return True


XDATA = numpy.linspace(0, 10, 10)


class EquationOperations():
    """Operations to be performed on equation items."""

    @staticmethod
    def execute(
        item: Graphs.EquationItem,
        name: str,
        figure_settings: Graphs.FigureSettings,
        _interaction_mode: Graphs.Mode,
        *args,
    ) -> tuple[bool, str]:
        """Execute the operation on the given item."""
        old_limits = figure_settings.get_limits().values()
        try:
            callback = getattr(EquationOperations, name)
            if name in ("normalize", "center", "transform"):
                args = [(
                    old_limits[item.get_xposition()],
                    old_limits[item.get_yposition() + 1],
                )] + list(args)
            equation = item.get_preprocessed_equation()
            equation = str(sympy.simplify(callback(equation, *args)))
            try:
                numexpr.evaluate(equation, local_dict={"x": XDATA})
            except (KeyError, SyntaxError, ValueError, TypeError) as e:
                raise misc.InvalidEquationError(
                    _(
                        "The operation on {name} "
                        "did not result in a plottable equation",
                    ).format(name=item.get_name()),
                ) from e
            item.set_equation(Graphs.prettify_equation(equation))
        except misc.InvalidEquationError as error:
            return False, error.message
        except (NotImplementedError, AttributeError, KeyError):
            return False, _("Operation not supported for equations.")
        return True, ""

    @staticmethod
    def translate_x(equation, offset) -> str:
        """Translate all selected data on the x-axis."""
        return re.sub(r"(?<!e)x(?!p)", f"(x+{offset})", equation)

    @staticmethod
    def translate_y(equation, offset) -> str:
        """Translate all selected data on the y-axis."""
        return f"({equation})+{offset}"

    @staticmethod
    def multiply_x(equation, multiplier: float) -> str:
        """Multiply all selected data on the x-axis."""
        return re.sub(r"(?<!e)x(?!p)", f"(x*{multiplier})", equation)

    @staticmethod
    def multiply_y(equation, multiplier: float) -> str:
        """Multiply all selected data on the y-axis."""
        return f"({equation})*{multiplier}"

    @staticmethod
    def normalize(equation, limits) -> str:
        """Normalize all selected data."""
        ydata = utilities.equation_to_data(equation, limits)[1]
        return f"({equation})/{max(ydata)}"

    @staticmethod
    def center(equation, limits, center_maximum: int) -> str:
        """
        Center all selected data.

        Depending on the key, will center either on the middle coordinate, or
        on the maximum value of the data
        """
        xdata, ydata = utilities.equation_to_data(equation, limits)
        if center_maximum == 0:  # Center at maximum Y
            x = misc.X
            equation = sympy.sympify(equation)
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
        return re.sub(r"(?<!e)x(?!p)", f"(x+{middle_value})", equation)

    @staticmethod
    def derivative(equation) -> str:
        """Calculate derivative of all selected data."""
        return str(sympy.diff(equation, misc.X))

    @staticmethod
    def integral(equation) -> str:
        """Calculate indefinite integral of all selected data."""
        return str(sympy.integrate(equation, misc.X))

    @staticmethod
    def fft(equation) -> str:
        """Perform Fourier transformation on all selected data."""
        k = sympy.Symbol("k")
        equation = str(sympy.fourier_transform(equation, misc.X, k))
        return equation.replace("k", "x")

    @staticmethod
    def inverse_fft(equation) -> str:
        """Perform Inverse Fourier transformation on all selected data."""
        k = sympy.Symbol("k")
        equation = str(sympy.fourier_transform(equation, misc.X, k))
        return equation.replace("k", "x")

    @staticmethod
    def transform(
        equation: str,
        limits: list,
        input_x: str,
        input_y: str,
        _discard: bool,
    ) -> str:
        """Perform custom transformation."""
        xdata, ydata = utilities.equation_to_data(equation, limits)
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

        equation = re.sub(r"(?<!e)x(?!p)", input_x, equation)
        return input_y.lower().replace("y", equation)


_return = (list[float], list[float], bool, bool)


class DataOperations():
    """Operations to be performed on data items."""

    @staticmethod
    def execute(
        item: Graphs.DataItem,
        name: str,
        figure_settings: Graphs.FigureSettings,
        interaction_mode: Graphs.Mode,
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
        if discard and interaction_mode == Graphs.Mode.SELECT:
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
            new_xdata = item.get_xdata().copy()
            new_ydata = item.get_ydata().copy()
            xerr = item.get_xerr()
            yerr = item.get_yerr()
            if xdata is None:  # If cut action was performed
                new_xdata = new_xdata[~mask]
                new_ydata = new_ydata[~mask]

                xerr = xerr[~mask] if xerr is not None else None
                yerr = yerr[~mask] if yerr is not None else None
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
                new_xdata, new_ydata = \
                    DataHelper.sort_data(new_xdata, new_ydata)
            item.set_data_tuple((new_xdata, new_ydata, xerr, yerr))
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
        return None, None, False, False

    @staticmethod
    def derivative(_item, xdata: list, ydata: list) -> _return:
        """Calculate derivative of all selected data."""
        dy_dx = numpy.gradient(ydata, xdata)
        return xdata, dy_dx, False, True

    @staticmethod
    def integral(_item, xdata: list, ydata: list) -> _return:
        """Calculate indefinite integral of all selected data."""
        indefinite_integral = scipy.integrate.cumulative_trapezoid(
            ydata,
            xdata,
            initial=0,
        )
        return xdata, indefinite_integral, False, True

    @staticmethod
    def fft(_item, xdata: list, ydata: list) -> _return:
        """Perform Fourier transformation on all selected data."""
        y_fourier = numpy.fft.fft(ydata)
        x_fourier = numpy.fft.fftfreq(len(xdata), xdata[1] - xdata[0])
        y_fourier = [value.real for value in y_fourier]
        return x_fourier, y_fourier, False, True

    @staticmethod
    def inverse_fft(_item, xdata: list, ydata: list) -> _return:
        """Perform Inverse Fourier transformation on all selected data."""
        y_fourier = numpy.fft.ifft(ydata)
        x_fourier = numpy.fft.fftfreq(len(xdata), xdata[1] - xdata[0])
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
                Graphs.preprocess_equation(input_x) + "+ 0*x",
                local_dict,
            ),
            numexpr.evaluate(
                Graphs.preprocess_equation(input_y) + "+ 0*y",
                local_dict,
            ),
            True,
            discard,
        )
