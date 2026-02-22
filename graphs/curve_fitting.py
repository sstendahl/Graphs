# SPDX-License-Identifier: GPL-3.0-or-later
"""Curve fitting module."""
from gettext import gettext as _

from gi.repository import Adw, Gio, Graphs

from graphs import canvas
from graphs.item import DataItem, FillItem

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
        super().__init__(window=window)
        Adw.StyleManager.get_default().connect("notify", self._load_canvas)

        style = Graphs.StyleManager.get_instance().get_system_style_params()

        xdata, ydata = item.props.data
        self._data = numpy.asarray(xdata), numpy.asarray(ydata)

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
            xdata=xdata,
            ydata=ydata,
            color=FIT_COLOR,
        )
        self.fill = FillItem.new(
            style,
            (xdata, ydata, ydata),
            color=FILL_COLOR,
            alpha=FILL_ALPHA,
        )
        self.residuals_item = DataItem.new(
            style,
            xdata=numpy.zeros(len(xdata)),
            ydata=numpy.zeros(len(ydata)),
            color=DATA_COLOR,
            linestyle=LINE_STYLE,
            markerstyle=MARKER_STYLE,
            markersize=MARKER_SIZE,
        )

        x_min, x_max = min(xdata), max(xdata)
        padding = (x_max - x_min) * 0.025
        self._xlim = (x_min - padding, x_max + padding)

        self._load_canvas()
        self.setup()
        self.present(window)

    def _load_canvas(self, *_args) -> None:
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
        sym_vars = sympy.symbols(variables)
        sym_params_map = dict(zip(variables, sym_vars))
        x_data, y_data = self._data
        equation = self.get_equation_string()
        try:
            symbolic = sympy.sympify(equation, locals=sym_params_map)
            func = sympy.lambdify(sym_vars, symbolic)
            params, param_cov = curve_fit(
                func, x_data, y_data,
                p0=self.get_p0(),
                bounds=self.get_bounds(),
                nan_policy="omit",
                method=self.get_settings().get_string("optimization"),
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
        n = len(y_data)
        fitted_y = func(x_data, *params)
        ss_res = numpy.sum((y_data - fitted_y)**2)
        ss_tot = numpy.sum((y_data - numpy.mean(y_data))**2)
        r2 = 1 - (ss_res / ss_tot)
        rmse = numpy.sqrt(ss_res / n)

        d_cov = numpy.sqrt(numpy.diagonal(param_cov))
        self.props.fit_result = Graphs.FitResult.new(params, d_cov, r2, rmse)

        residuals = y_data - fitted_y
        self.residuals_item.props.data = x_data, residuals

        # Substitute each free variables with the calculated value.
        values = dict(zip(free_vars, params))
        fitted_eq = str(sympy.simplify(symbolic.subs(values)))
        fitted_eq = Graphs.prettify_equation(fitted_eq)
        self.props.fitted_equation_string = fitted_eq

        x_fit = numpy.linspace(*self._xlim, 5000)
        y_fit = func(x_fit, *params)

        self.fitted_curve.props.data = x_fit, y_fit
        self.fitted_curve.set_name(f"Y = {fitted_eq}")

        # Calculate and update confidence band for error propagation.
        jacobian = numpy.zeros((x_fit.size, len(params)))

        for i, name in enumerate(free_vars):
            deriv = sympy.diff(symbolic, sym_params_map[name])
            f_deriv = sympy.lambdify(sym_vars, deriv, "numpy")
            jacobian[:, i] = f_deriv(x_fit, *params)

        variance = numpy.sum((jacobian @ param_cov) * jacobian, axis=1)

        conf_level = self.get_settings().get_enum("confidence")
        std_dev_y = numpy.sqrt(numpy.abs(variance))
        confidence_band = std_dev_y * conf_level

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

        all_y = [y for y in (*y_lower, *y_upper, *y_data) if numpy.isfinite(y)]
        y_min, y_max = min(all_y), max(all_y)

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
        xdata = self.data_curve.get_xdata()
        residuals = numpy.zeros(len(xdata))
        self.residuals_item.props.data = xdata, residuals

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
