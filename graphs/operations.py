# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data transformations."""
import logging
import math
import re
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs import ast, misc, utilities

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
        data.optimize_limits()
        data.add_history_state()


def get_selected_limits(
    figure_settings: Graphs.FigureSettings,
    interaction_mode: Graphs.Mode,
    position: Graphs.XPosition,
) -> tuple[float, float]:
    """Get the min and max value of the item within the selected range."""
    if position == Graphs.XPosition.BOTTOM:
        min_x = figure_settings.get_min_bottom()
        max_x = figure_settings.get_max_bottom()
        scale = figure_settings.get_bottom_scale()
    else:
        min_x = figure_settings.get_min_top()
        max_x = figure_settings.get_max_top()
        scale = figure_settings.get_top_scale()
    if interaction_mode != Graphs.Mode.SELECT:
        return min_x, max_x
    new_min = Graphs.get_value_at_fraction(
        figure_settings.get_min_selected(),
        min_x,
        max_x,
        scale,
    )
    new_max = Graphs.get_value_at_fraction(
        figure_settings.get_max_selected(),
        min_x,
        max_x,
        scale,
    )
    return new_min, new_max


def _has_pole(values: numpy.ndarray) -> bool:
    """
    Check whether sampled equation values shoot off towards infinity.

    Splits the samples into four sets and compares maximum deviation from the
    median. Near a pole the deviation will differ strongly between sets.
    """
    # Crashes on numpy.max() if one of the sets is empty
    if values.size < 4:
        return False

    deviation = numpy.abs(values - numpy.median(values))
    max_deviations = []
    for start in range(4):
        max_deviations.append(numpy.max(deviation[start::4]))
    return max(max_deviations) > 2 * min(max_deviations)


def _get_y_range(item, settings, mode, scale: Graphs.Scale) -> tuple | None:
    """Get (item, low, high, mask) in axis units, None if there is no data."""
    xposition = item.get_xposition()
    limits = get_selected_limits(settings, mode, xposition)
    mask = None
    if isinstance(item, Graphs.EquationItem):
        if xposition == Graphs.XPosition.BOTTOM:
            xscale = settings.get_bottom_scale()
        else:
            xscale = settings.get_top_scale()
        ydata = utilities.equation_to_data(
            item.get_equation(), limits, scale=xscale,
        )[1]
    else:
        xdata, ydata = utilities.get_xydata(item.get_data())
        if mode == Graphs.Mode.SELECT:
            mask = (xdata >= min(limits)) & (xdata <= max(limits))
            ydata = ydata[mask]
    with numpy.errstate(divide="ignore", invalid="ignore"):
        if scale == Graphs.Scale.LOG:
            values = numpy.log10(ydata)
        elif scale == Graphs.Scale.LOG2:
            values = numpy.log2(ydata)
        else:
            values = ydata
    finite = values[numpy.isfinite(values)]
    if finite.size == 0:
        return None
    if isinstance(item, Graphs.EquationItem) and _has_pole(finite):
        # Don't let the spike decide the spacing
        low, high = numpy.percentile(finite, (5, 95))
    else:
        low, high = finite.min(), finite.max()
    return item, float(low), float(high), mask


def _stack(y_ranges: list, scale: Graphs.Scale, move_first: bool) -> list:
    """Get (item, mask, value) for the items of one y-axis."""
    heights = [high - low for _item, low, high, _mask in y_ranges]
    gap = 0.1 * max(heights)
    if gap == 0:  # flat curves, use their distance from zero instead
        levels = [abs(high) for _item, _low, high, _mask in y_ranges]
        gap = 0.1 * max(levels) or 1  # 1 when all lines are y = 0

    log = scale in (Graphs.Scale.LOG, Graphs.Scale.LOG2)
    base = 2 if scale == Graphs.Scale.LOG2 else 10
    decimals = 2 - math.floor(math.log10(gap))
    if log:
        digits = 1 - math.floor(math.log10(base ** (0.01 * gap) - 1))

    old_top = new_top = y_ranges[0][2]
    shifts = []
    for item, low, high, mask in y_ranges if move_first else y_ranges[1:]:
        offset = new_top + max(0, low - old_top) + gap - low
        if not log:
            value = offset = round(offset, decimals)
        else:
            factor = base ** offset
            value = round(factor, digits - math.floor(math.log10(factor)))
            offset = math.log(value, base)
        shifts.append((item, mask, value))
        old_top = max(old_top, high)
        new_top = max(new_top, high + offset)
    return shifts


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
                else:
                    continue
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

            data.optimize_limits()
            data.add_history_state()

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

            lims = get_selected_limits(settings, mode, item.get_xposition())

            if isinstance(item, Graphs.EquationItem):
                equation = item.get_equation()
                xdata, ydata = utilities.equation_to_data(equation, lims)
                new_xerr, new_yerr = None, None
            elif isinstance(item, Graphs.DataItem):
                item_data = item.get_data()
                xdata, ydata = utilities.get_xydata(item_data)
                xerr, yerr = utilities.get_xyerr(item_data)
                if mode == Graphs.Mode.SELECT:
                    startx, stopx = lims
                    # If startx and stopx are not out of range, that is,
                    # if the item data is within the highlight
                    if stopx < min(xdata) or startx > max(xdata):
                        continue
                    mask = numpy.greater_equal(xdata, startx)
                    mask &= numpy.less_equal(xdata, stopx)
                    xdata, ydata = xdata[mask], ydata[mask]

                if xerr is not None and new_xerr is not None:
                    new_xerr.append(xerr)
                    some_x = True
                else:
                    new_xerr = None
                if yerr is not None and new_yerr is not None:
                    new_yerr.append(yerr)
                    some_y = True
                else:
                    new_yerr = None

            new_xdata.append(xdata)
            new_ydata.append(ydata)

        if not new_xdata or not new_ydata:
            window.add_toast_string(_("No data found in highlighted area"))
            return False

        if (some_x and new_xerr is None) or (some_y and new_yerr is None):
            msg = _("Some items lack error bars; they will be discarded")
            window.add_toast_string(msg)

        new_xdata = numpy.concatenate(new_xdata)
        idx = numpy.argsort(new_xdata)
        new_item = Graphs.ItemFactory.new_data_item(
            data.get_selected_style_params(),
            new_xdata[idx],
            numpy.concatenate(new_ydata)[idx],
            None if new_xerr is None else numpy.concatenate(new_xerr)[idx],
            None if new_yerr is None else numpy.concatenate(new_yerr)[idx],
        )
        new_item.set_name(_("Combined Data"))
        data.add_items([new_item])
        return True

    @staticmethod
    def shift(window: Graphs.Window) -> bool:
        """Stack the selected items vertically, so no two share y values."""
        mode = window.get_mode()
        data = window.get_data()
        settings = data.get_figure_settings()
        scales = settings.get_left_scale(), settings.get_right_scale()
        groups = ([], [])  # (items on left axes, items on right axis)
        for item in data:
            if item.get_selected() and isinstance(
                item, (Graphs.EquationItem, Graphs.DataItem),
            ):
                y = int(item.get_yposition())
                y_range = _get_y_range(item, settings, mode, scales[y])
                if y_range is not None:
                    groups[y].append(y_range)
        if not any(groups):
            if mode == Graphs.Mode.SELECT:
                msg = _("No data found within the highlighted area")
            window.add_toast_string(msg)
            return False

        shifts = [
            (shift, scale) for group, scale in zip(groups, scales) if group
            for shift in _stack(
                group, scale, len(group) == 1 or mode == Graphs.Mode.SELECT,
            )
        ]
        for (item, mask, value), scale in shifts:
            log = scale in (Graphs.Scale.LOG, Graphs.Scale.LOG2)
            if isinstance(item, Graphs.EquationItem):
                equation = Graphs.ast_to_expression(item.get_equation())
                if not log:
                    equation = f"({equation}) + {value!r}"
                else:
                    equation = f"{value!r} * ({equation})"
                item.set_equation(Graphs.PythonHelper.simplify_expression(
                    Graphs.expression_to_ast(equation),
                ))
                continue
            holder = item.get_data()
            xdata, ydata = utilities.get_xydata(holder)
            xerr, yerr = utilities.get_xyerr(holder)
            mask = slice(None) if mask is None else mask
            ydata = ydata.copy()
            if not log:
                ydata[mask] += value
            else:
                ydata[mask] *= value
                if yerr is not None:
                    # Scale the error bars with the data. get_xyerr returns a
                    # read-only view of the item's data, so use copy instead.
                    yerr = yerr.copy()
                    yerr[mask] *= value
            item.set_data(Graphs.DataHolder.new(xdata, ydata, xerr, yerr))
        return True


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
                xindex = item.get_xposition() * 2
                args = [(
                    old_limits[xindex],
                    old_limits[xindex + 1],
                )] + list(args)
            equation = ast.sympify(item.get_equation())
            equation = callback(equation, *args)
            equation = Graphs.expression_to_ast(str(equation))
            if not Graphs.math_tools_validate_expression(equation):
                message = _(
                    "The operation on {name} "
                    "did not result in a plottable equation",
                ).format(name=item.get_name())
                return False, message
            item.set_equation(equation)
        except (NotImplementedError, AttributeError, KeyError):
            return False, _("Operation not supported for equations.")
        return True, ""

    @staticmethod
    def translate_x(equation: sympy.Expr, offset: float) -> sympy.Expr:
        """Translate all selected data on the x-axis."""
        return equation.subs(misc.X, misc.X - offset)

    @staticmethod
    def translate_y(equation: sympy.Expr, offset: float) -> sympy.Expr:
        """Translate all selected data on the y-axis."""
        return equation + offset

    @staticmethod
    def multiply_x(equation: sympy.Expr, multiplier: float) -> sympy.Expr:
        """Multiply all selected data on the x-axis."""
        return equation.subs(misc.X, misc.X / multiplier)

    @staticmethod
    def multiply_y(equation: sympy.Expr, multiplier: float) -> sympy.Expr:
        """Multiply all selected data on the y-axis."""
        return equation * multiplier

    @staticmethod
    def normalize(
        equation: sympy.Expr,
        limits: tuple[float, float],
    ) -> sympy.Expr:
        """Normalize all selected data."""
        domain = sympy.Interval(*limits)
        try:
            magnitude = float(sympy.maximum(equation, misc.X, domain))
        except (TypeError, ValueError, NotImplementedError, OverflowError):
            magnitude = numpy.nan
        if not numpy.isfinite(magnitude) or magnitude <= 0:
            _xdata, ydata = utilities.equation_to_data(
                Graphs.expression_to_ast(str(equation)),
                limits,
            )
            magnitude = numpy.max(numpy.abs(ydata), initial=0)
        if magnitude == 0:
            return equation
        return equation / magnitude

    @staticmethod
    def center(
        equation: sympy.Expr,
        limits: tuple[float, float],
        center_maximum: int,
    ) -> sympy.Expr:
        """
        Center all selected data.

        Depending on the key, will center either on the middle coordinate, or
        on the maximum value of the data
        """
        x = misc.X
        low, high = limits
        if center_maximum == 0:  # Center at maximum Y
            derivative = sympy.diff(equation, x)
            critical_points = sympy.solveset(
                derivative,
                x,
                domain=sympy.Interval(low, high),
            )

            candidates = []
            candidates.extend([low, high])

            if isinstance(critical_points, sympy.FiniteSet):
                for point in critical_points:
                    try:
                        candidates.append(float(point))
                    except TypeError:
                        continue

            values = [equation.subs(x, c) for c in candidates]

            best_index = max(range(len(values)), key=lambda i: values[i])
            middle_value = candidates[best_index]
        elif center_maximum == 1:  # Center at middle
            middle_value = sympy.Rational(1, 2) * (low + high)
        return equation.subs(x, x + middle_value)

    @staticmethod
    def derivative(equation: sympy.Expr) -> sympy.Expr:
        """Calculate derivative of all selected data."""
        return sympy.diff(equation, misc.X)

    @staticmethod
    def integral(equation: sympy.Expr) -> sympy.Expr:
        """Calculate indefinite integral of all selected data."""
        return sympy.integrate(equation, misc.X)

    @staticmethod
    def fft(equation: sympy.Expr) -> sympy.Expr:
        """Perform Fourier transformation on all selected data."""
        k = sympy.Symbol("k")
        equation = sympy.fourier_transform(equation, misc.X, k)
        return equation.subs(k, misc.X)

    @staticmethod
    def inverse_fft(equation: sympy.Expr) -> sympy.Expr:
        """Perform Inverse Fourier transformation on all selected data."""
        k = sympy.Symbol("k")
        equation = sympy.fourier_transform(equation, misc.X, k)
        return equation.subs(k, misc.X)

    @staticmethod
    def transform(
        equation: sympy.Expr,
        limits: tuple[float, float],
        input_x: str,
        input_y: str,
        _discard: bool,
    ) -> str:
        """Perform custom transformation."""
        xdata, ydata = utilities.equation_to_data(
            Graphs.expression_to_ast(str(equation)),
            limits,
        )
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

        equation = re.sub(
            r"(?<!e)x(?!p)",
            lambda _match: f"({input_x})",
            str(equation),
        )
        return input_y.lower().replace("y", str(equation))


_return = (numpy.ndarray, numpy.ndarray, bool, bool)


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
        data = item.get_data()
        xdata, ydata = utilities.get_xydata(data)
        if interaction_mode == Graphs.Mode.SELECT:
            startx, stopx = get_selected_limits(
                figure_settings,
                interaction_mode,
                item.get_xposition(),
            )
            # If startx and stopx are not out of range, that is,
            # if the item data is within the highlight
            if stopx < min(xdata) or startx > max(xdata):
                return False, _("No data found within the highlighted area")
            mask = numpy.greater_equal(xdata, startx)
            mask &= numpy.less_equal(xdata, stopx)
            if not mask.any():
                return False, _("No data found within the highlighted area")
            xdata, ydata = xdata[mask], ydata[mask]
        try:
            callback = getattr(DataOperations, name)
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
        xerr, yerr = utilities.get_xyerr(data)
        if interaction_mode == Graphs.Mode.SELECT:
            if discard:
                logging.debug("Discard is true")
                message = _(
                    "Data that was outside of the highlighted area has"
                    " been discarded",
                )
            elif new_xdata is None:  # If cut action was performed
                new_xdata, new_ydata = utilities.get_xydata(data)
                new_xdata = new_xdata[~mask]
                new_ydata = new_ydata[~mask]
                xerr = xerr[~mask] if xerr is not None else None
                yerr = yerr[~mask] if yerr is not None else None
            else:
                logging.debug("Discard is false")
                xdata, ydata = utilities.get_xydata(data)
                xdata = xdata.copy()
                ydata = ydata.copy()
                xdata[mask] = new_xdata
                ydata[mask] = new_ydata
                new_xdata, new_ydata = xdata, ydata
        if sort:
            logging.debug("Sorting data")
            idx = numpy.argsort(new_xdata)
            new_xdata, new_ydata = new_xdata[idx], new_ydata[idx]
        item.set_data(Graphs.DataHolder.new(new_xdata, new_ydata, xerr, yerr))
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
        return xdata + offset, ydata, True, False

    @staticmethod
    def translate_y(_item, xdata: list, ydata: list, offset: float) -> _return:
        """
        Translate all selected data on the y-axis.

        Amount to be shifted is equal to the value in the translate_y entry
        widget.
        Will show a toast if a ValueError is raised, typically when a user
        entered an invalid number (e.g. comma instead of point separators)
        """
        return xdata, ydata + offset, False, False

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
        return xdata * multiplier, ydata, True, False

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
        return xdata, ydata * multiplier, False, False

    @staticmethod
    def normalize(_item, xdata: list, ydata: list) -> _return:
        """Normalize all selected data."""
        return xdata, ydata / max(ydata), False, False

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
            middle_index = numpy.argmax(ydata)
            middle_value = xdata[middle_index]
        elif center_maximum == 1:  # Center at middle
            middle_value = (min(xdata) + max(xdata)) / 2
        return xdata - middle_value, ydata, True, False

    @staticmethod
    def cut(_item, _xdata, _ydata) -> _return:
        """Cut selected data over the span that is selected."""
        return None, None, False, False

    @staticmethod
    def derivative(_item, xdata: list, ydata: list) -> _return:
        """Calculate derivative of all selected data."""
        return xdata, numpy.gradient(ydata, xdata), False, True

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
        ld = {
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

        expr_x = ast.sympify(Graphs.expression_to_ast(input_x)).subs(ld)
        expr_y = ast.sympify(Graphs.expression_to_ast(input_y)).subs(ld)

        f_x = sympy.lambdify((misc.X, misc.Y), expr_x, modules="scipy")
        f_y = sympy.lambdify((misc.X, misc.Y), expr_y, modules="scipy")

        out_x = f_x(xdata, ydata)
        out_y = f_y(xdata, ydata)

        return out_x, out_y, True, discard
