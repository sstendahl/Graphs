# SPDX-License-Identifier: GPL-3.0-or-later
"""Curve fitting module."""
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs import canvas
from graphs.item import DataItem, FillItem

import numexpr

import numpy

from scipy.optimize import _minpack, curve_fit

import sympy

DATA_COLOR = "#1A5FB4"
FIT_COLOR = "#A51D2D"
FILL_COLOR = "#62A0EA"
FILL_ALPHA = 0.25
MARKER_STYLE = 1
MARKER_SIZE = 13
LINE_STYLE = 0


class CurveFittingDialog(Graphs.CurveFittingDialog):
    """Class for displaying the Curve Fitting dialog."""

    __gtype_name__ = "GraphsPythonCurveFittingDialog"

    def __init__(self, window: Graphs.Window, item: Graphs.Item):
        """Initialize the curve fitting dialog."""
        xdata, ydata = item.get_xydata()
        self._data = xdata, ydata
        x_min, x_max = min(xdata), max(xdata)
        padding = (x_max - x_min) * 0.025
        self._xlim = (x_min - padding, x_max + padding)
        self._x_fit = numpy.linspace(*self._xlim, 5000)

        style = Graphs.StyleManager.get_instance().get_system_style_params()
        self.data_curve = DataItem.new(
            style,
            xdata=xdata,
            ydata=ydata,
            name=item.get_name(),
            color=DATA_COLOR,
            linestyle=LINE_STYLE,
            markerstyle=MARKER_STYLE,
            markersize=MARKER_SIZE,
        )
        self.fitted_curve = DataItem.new(
            style,
            xdata=[],
            ydata=[],
            color=FIT_COLOR,
        )
        self.fill = FillItem.new(
            style,
            ([], [], []),
            color=FILL_COLOR,
            alpha=FILL_ALPHA,
        )
        self.residuals_item = DataItem.new(
            style,
            xdata=[],
            ydata=[],
            color=DATA_COLOR,
            linestyle=LINE_STYLE,
            markerstyle=MARKER_STYLE,
            markersize=MARKER_SIZE,
        )

        super().__init__(window=window)
        self.present(window)

    def _load_canvas(self) -> None:
        """Initialize and set main canvas."""
        settings = self.props.window.get_data().get_figure_settings()
        style = Graphs.StyleManager.get_instance().get_system_style_params()

        listmodel = Gio.ListStore.new(Graphs.Item)
        listmodel.append(self.fitted_curve)
        listmodel.append(self.fill)
        listmodel.append(self.data_curve)
        cv = canvas.Canvas(style, listmodel, interactive=False)
        ax = cv.figure.axis
        ax.set(
            xlabel=settings.get_bottom_label(),
            ylabel=settings.get_left_label(),
            xlim=self._xlim,
        )
        self.set_canvas(cv)

        listmodel = Gio.ListStore.new(Graphs.Item)
        listmodel.append(self.residuals_item)
        cv = canvas.Canvas(style, listmodel, interactive=False)
        ax = cv.figure.axis
        ax.set_ylabel(_("Residuals"))
        ax.set_xlabel(settings.get_bottom_label())
        ax.axhline(y=0, color="black", linestyle="--", linewidth=0.5)
        ax.set_xlim(*self._xlim)
        ax.set_ylim(-1, 1)
        cv.figure.props.legend = False
        self.set_residuals_canvas(cv)

    def _fit_curve(self) -> None:
        """Handle fit curve request."""
        free_vars = self.get_free_vars()
        variables = ["x"] + free_vars
        sym_params_map = dict(zip(variables, sympy.symbols(variables)))
        x_data, y_data = self._data
        equation = self.get_equation_string()
        settings = self.get_settings()

        def func(*params) -> numpy.ndarray:
            return numexpr.evaluate(equation, dict(zip(variables, params)))

        try:
            symbolic = sympy.sympify(equation, locals=sym_params_map)
            params, param_cov = curve_fit(
                func, x_data, y_data,
                p0=self.get_p0(),
                bounds=self.get_bounds(),
                nan_policy="omit",
                method=settings.get_string("optimization"),
            )
        except (sympy.SympifyError, TypeError, SyntaxError):
            self.set_results(Graphs.CurveFittingError.EQUATION)
            return
        except (RuntimeError, _minpack.error):
            self.set_results(Graphs.CurveFittingError.CONVERGENCE)
            return
        except (ValueError, ZeroDivisionError, OverflowError):
            self.set_results(Graphs.CurveFittingError.DOMAIN)
            return

        if numpy.any(numpy.isinf(param_cov)):
            self.set_results(Graphs.CurveFittingError.SINGULAR)
            return

        # Calculate statistics
        residuals = y_data - func(x_data, *params)
        ss_res = numpy.sum(residuals**2)
        ss_tot = numpy.sum((y_data - numpy.mean(y_data))**2)
        d_cov = numpy.sqrt(numpy.diagonal(param_cov))
        r2 = 1 - (ss_res / ss_tot)
        rmse = numpy.sqrt(ss_res / y_data.size)
        self.props.fit_result = Graphs.FitResult.new(params, d_cov, r2, rmse)
        self.residuals_item.set_xydata((x_data, residuals))

        # Substitute each free variables with the calculated value.
        values = dict(zip(free_vars, params))
        fitted_eq = str(sympy.simplify(symbolic.subs(values)))
        fitted_eq = Graphs.prettify_equation(fitted_eq)
        self.props.fitted_equation_string = fitted_eq

        x_fit = self._x_fit
        y_fit = func(x_fit, *params)
        if numpy.ndim(y_fit) == 0:
            y_fit = numpy.full(x_fit.size, y_fit.item())

        self.fitted_curve.set_xydata((x_fit, y_fit))
        self.fitted_curve.set_name(f"Y = {fitted_eq}")

        # Calculate and update confidence band for error propagation.
        local_dict = {"x": x_fit} | values
        jacobian = numpy.column_stack([
            numpy.full(x_fit.size, g) if numpy.ndim(
                g := numexpr.evaluate(
                    str(sympy.diff(symbolic, sym_params_map[name])),
                    local_dict,
                ),
            ) == 0 else g for name in free_vars
        ])
        variance = numpy.sum(jacobian * (jacobian @ param_cov), axis=1)

        std_dev_y = numpy.sqrt(numpy.abs(variance))
        confidence_band = std_dev_y * settings.get_enum("confidence")

        y_upper = y_fit + confidence_band
        y_lower = y_fit - confidence_band
        self.fill.props.data = (x_fit, y_lower, y_upper)

        # Show fill and fit again after successful fit
        cv = self.get_canvas()
        ax = cv.figure.axis
        for line in ax.lines[1:]:
            line.set_visible(True)
        for collection in ax.collections:
            collection.set_visible(True)

        all_y = numpy.concatenate((y_lower, y_upper, y_data))
        all_y = all_y[numpy.isfinite(all_y)]
        y_min, y_max = all_y.min(), all_y.max()

        padding = (y_max - y_min) * 0.025
        ax.set_ylim(y_min - padding, y_max + padding)
        cv.queue_draw()

        cv = self.get_residuals_canvas()
        ax = cv.figure.axis
        ax.lines[0].set_visible(True)
        max_val = abs(residuals).max()
        if max_val > 0:
            y_lim = max_val * 1.1
            ax.set_ylim(-y_lim, y_lim)
        else:
            ax.set_ylim(-1, 1)
        cv.queue_draw()

        self.set_results(Graphs.CurveFittingError.NONE)

    def _clear_fit(self) -> None:
        """Clear all fit-related data by hiding curves."""
        cv = self.get_residuals_canvas()
        ax = cv.figure.axis
        ax.lines[0].set_visible(False)
        ax.set_ylim(-1, 1)

        # Hide all lines except the first one (data curve)
        cv = self.get_canvas()
        ax = cv.figure.axis
        for line in ax.lines[1:]:
            line.set_visible(False)
        # Hide all collections (fill)
        for collection in ax.collections:
            collection.set_visible(False)
        cv.queue_draw()
