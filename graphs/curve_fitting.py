# SPDX-License-Identifier: GPL-3.0-or-later
"""Curve fitting module."""
from gi.repository import Graphs

from graphs import ast

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

        super().__init__(window=window)
        self.setup(item)
        self.present(window)

    def _load_canvas(self) -> None:
        """Initialize and set main canvas."""
        self.props.canvas.figure.axis.set(xlim=self._xlim)

        ax = self.props.residuals_canvas.figure.axis
        ax.axhline(y=0, color="black", linestyle="--", linewidth=0.5)
        ax.set_xlim(*self._xlim)

    def _fit_curve(self) -> None:
        """Handle fit curve request."""
        free_vars = self.get_free_vars()
        variables = ["x"] + free_vars
        sym_vars = sympy.symbols(variables)
        sym_params_map = dict(zip(variables, sym_vars))
        x_data, y_data = self._data
        expression = self.get_ast()
        settings = self.get_settings()

        try:
            symbolic = ast.sympify(expression)
            func = sympy.lambdify(sym_vars, symbolic, modules="scipy")
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
        self.props.residuals_canvas_items[0].set_xydata((x_data, residuals))

        # Substitute each free variables with the calculated value.
        values = dict(zip(free_vars, params))
        fitted_eq = str(sympy.simplify(symbolic.subs(values)))
        fitted_eq = Graphs.expression_to_ast(fitted_eq)
        fitted_eq = Graphs.ast_to_expression(fitted_eq)
        self.props.fitted_equation_string = fitted_eq

        x_fit = self._x_fit
        y_fit = func(x_fit, *params)
        if numpy.ndim(y_fit) == 0:
            y_fit = numpy.full(x_fit.size, y_fit.item())

        fitted_curve = self.props.main_canvas_items[0]
        fitted_curve.set_xydata((x_fit, y_fit))
        fitted_curve.set_name(f"Y = {fitted_eq}")

        # Calculate and update confidence band for error propagation.
        jacobian = numpy.column_stack([
            numpy.full(x_fit.size, g) if numpy.ndim(
                g := sympy.lambdify(
                    sym_vars,
                    sympy.diff(symbolic, sym_params_map[name]),
                    modules="scipy",
                )(x_fit, *params),
            ) == 0 else g for name in free_vars
        ])
        variance = numpy.sum(jacobian * (jacobian @ param_cov), axis=1)

        std_dev_y = numpy.sqrt(numpy.abs(variance))
        confidence_band = std_dev_y * settings.get_enum("confidence")

        y_upper = y_fit + confidence_band
        y_lower = y_fit - confidence_band
        fill = self.props.main_canvas_items[1]
        fill.set_data_tuple((x_fit, y_lower, y_upper))

        # Show fill and fit again after successful fit
        cv = self.get_canvas()
        ax = cv.figure.axis

        all_y = numpy.concatenate((y_lower, y_upper, y_data))
        all_y = all_y[numpy.isfinite(all_y)]
        y_min, y_max = all_y.min(), all_y.max()

        padding = (y_max - y_min) * 0.025
        ax.set_ylim(y_min - padding, y_max + padding)
        cv.queue_draw()

        ax = self.get_residuals_canvas().figure.axis
        max_val = abs(residuals).max()
        if max_val > 0:
            y_lim = max_val * 1.1
            ax.set_ylim(-y_lim, y_lim)
        else:
            ax.set_ylim(-1, 1)
        cv.queue_draw()

        self.set_results(Graphs.CurveFittingError.NONE)
