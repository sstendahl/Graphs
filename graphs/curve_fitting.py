# SPDX-License-Identifier: GPL-3.0-or-later
"""Curve fitting module."""
import contextlib
import re
from gettext import gettext as _

from gi.repository import Adw, GLib, Gio, Graphs

from graphs import canvas, utilities
from graphs.item import DataItem, EquationItem, FillItem

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
        Adw.StyleManager.get_default().connect("notify", self.load_canvas)

        style = Graphs.StyleManager.get_instance().get_system_style_params()

        self.data_curve = DataItem.new(
            style,
            xdata=item.get_xdata(),
            ydata=item.get_ydata(),
            name=item.get_name(),
            color=DATA_COLOR,
        )
        self.data_curve.linestyle = LINE_STYLE
        self.data_curve.markerstyle = MARKER_STYLE
        self.data_curve.markersize = MARKER_SIZE

        self.fitted_curve = EquationItem.new(style, "x", color=FIT_COLOR)
        self.fill = FillItem.new(
            style,
            (
                self.data_curve.get_xdata(),
                self.data_curve.get_ydata(),
                self.data_curve.get_ydata(),
            ),
            color=FILL_COLOR,
            alpha=FILL_ALPHA,
        )

        self._items = Gio.ListStore.new(Graphs.Item)
        self._items.append(self.fitted_curve)
        self._items.append(self.fill)
        self._items.append(self.data_curve)

        self._residuals_items = Gio.ListStore.new(Graphs.Item)
        self.residuals_item = DataItem.new(
            style,
            xdata=numpy.zeros(len(self.data_curve.get_xdata())),
            ydata=numpy.zeros(len(self.data_curve.get_xdata())),
            color=DATA_COLOR,
            linestyle=LINE_STYLE,
            markerstyle=MARKER_STYLE,
            markersize=MARKER_SIZE,
        )
        self._residuals_items.append(self.residuals_item)

        x_data = numpy.asarray(self.data_curve.get_xdata())
        x_min, x_max = x_data.min(), x_data.max()
        x_range = x_max - x_min
        padding = x_range * 0.025
        self._xlim = (x_min - padding, x_max + padding)

        self.setup()
        self.load_canvas()
        self.present(window)

    def load_canvas(self, *_args) -> None:
        """Initialize and set main canvas."""
        window_data = self.props.window.get_data()
        settings = window_data.get_figure_settings()
        style = Graphs.StyleManager.get_instance().get_system_style_params()
        cv = canvas.Canvas(style, self._items, interactive=False)
        ax = cv.figure.axis
        ax.set(
            xlabel=settings.get_property("bottom_label"),
            ylabel=settings.get_property("left_label"),
            xlim=self._xlim,
        )
        self.set_canvas(cv)
        self._load_residuals_canvas()
        if self.get_confirm_button().get_sensitive():
            self._clear_fit()

    def _load_residuals_canvas(self):
        """Initialize and set residuals canvas."""
        style = Graphs.StyleManager.get_instance().get_system_style_params()
        settings = self.props.window.get_data().get_figure_settings()

        cv = canvas.Canvas(style, self._residuals_items, interactive=False)
        ax = cv.figure.axis
        ax.set_ylabel(_("Residuals"))
        ax.set_xlabel(settings.get_property("bottom_label"))
        ax.axhline(y=0, color="black", linestyle="--", linewidth=0.5)
        ax.set_xlim(*self._xlim)
        if ax.get_legend():
            ax.get_legend().remove()
        self.set_residuals_canvas(cv)
        self._set_residual_canvas_scale()

    def update_canvas_data(self):
        """Update existing canvas data."""
        cv = self.get_canvas()
        if not cv:  # cv does not exist yet during setup phase
            return
        ax = cv.figure.axis

        equation = self.fitted_curve.equation
        _xfit, yfit = utilities.equation_to_data(equation, self._xlim)
        _xfill, yfill_low, yfill_high = self.fill.props.data
        ydata = self.data_curve.get_ydata()
        all_y = [*yfit, *yfill_low, *yfill_high, *ydata]
        all_y = [y for y in all_y if numpy.isfinite(y)]
        y_min, y_max = min(all_y), max(all_y)

        padding = (y_max - y_min) * 0.025
        ax.set_ylim(y_min - padding, y_max + padding)

        cv.queue_draw()

    def _fit_curve(self) -> None:
        """Handle fit curve request."""
        free_vars = self.props.fitting_parameters.get_free_vars()
        variables = ["x"] + free_vars
        sym_vars = sympy.symbols(variables)
        equation = self.get_equation_string()
        try:
            symbolic = sympy.sympify(
                equation,
                locals=dict(zip(variables, sym_vars)),
            )
            func = sympy.lambdify(sym_vars, symbolic)
        except (sympy.SympifyError, TypeError, SyntaxError):
            self.set_results(Graphs.CurveFittingError.EQUATION)
            return

        x_data = numpy.asarray(self.data_curve.get_xdata())
        y_data = numpy.asarray(self.data_curve.get_ydata())

        try:
            params, param_cov = curve_fit(
                func, x_data, y_data,
                p0=self.props.fitting_parameters.get_p0(),
                bounds=self.props.fitting_parameters.get_bounds(),
                nan_policy="omit",
                method=self.get_settings().get_string("optimization"),
            )

            if numpy.any(numpy.isinf(param_cov)):
                self.set_results(Graphs.CurveFittingError.SINGULAR)
                return

        except (RuntimeError, _minpack.error):
            self.set_results(Graphs.CurveFittingError.CONVERGENCE)
            return
        except (ValueError, TypeError, ZeroDivisionError, OverflowError):
            self.set_results(Graphs.CurveFittingError.DOMAIN)
            return

        # Calculate statistics
        n = len(y_data)
        fitted_y = func(x_data, *params)
        ss_res = numpy.sum((y_data - fitted_y)**2)
        ss_tot = numpy.sum((y_data - numpy.mean(y_data))**2)
        r2 = 1 - (ss_res / ss_tot)
        rmse = numpy.sqrt(ss_res / n)

        self._covariance = param_cov
        diag_cov = numpy.sqrt(numpy.diagonal(param_cov))
        self.props.fit_result = Graphs.FitResult.new(
            params,
            diag_cov,
            y_data - fitted_y,
            f"{r2:.3g}",
            f"{rmse:.3g}",
        )

        # Substitute each free variables with the calculated value.
        eq_name = equation.lower()
        for var, param_value in zip(free_vars, params):
            var_pattern = rf"\b{re.escape(var)}\b"
            equation = re.sub(var_pattern, f"({param_value})", equation)
            rounded = f"{param_value:.3g}"
            eq_name = re.sub(var_pattern, f"{rounded}", eq_name)

        self.fitted_curve.equation = equation
        self.fitted_curve.set_name(f"Y = {Graphs.prettify_equation(eq_name)}")

        # Show fill and fit again after successful fit
        cv = self.get_canvas()
        if self.get_confirm_button().get_sensitive() and cv:
            for line in cv.figure.axis.lines[1:]:
                line.set_visible(True)
            for collection in cv.figure.axis.collections:
                collection.set_visible(True)
            self._update_residuals()
            self.load_canvas()

        # Update all UI components
        self._update_residuals()
        self._update_confidence_band()
        self.update_canvas_data()
        self.set_results(Graphs.CurveFittingError.NONE)


    def _update_residuals(self) -> None:
        """Update residuals plot."""
        xdata = numpy.asarray(self.data_curve.get_xdata())
        if self.props.fit_result is None:
            residuals = numpy.zeros(len(self.data_curve.get_xdata()))
        else:
            residuals = self.props.fit_result.get_residuals()
        self.residuals_item.props.data = xdata, residuals
        cv = self.get_residuals_canvas()
        if not cv:
            return

        self._set_residual_canvas_scale()
        if legend := cv.figure.axis.get_legend():
            legend.remove()

    def _set_residual_canvas_scale(self) -> None:
        """Set the scaling for the residual canvas."""
        ax = self.get_residuals_canvas().figure.axis
        if len(self._residuals_items) > 0:
            y = numpy.asarray(self.residuals_item.get_ydata())
            max_val = abs(y).max()
            if max_val > 0:
                y_lim = max_val * 1.1
                ax.set_ylim(-y_lim, y_lim)

    def update_confidence_band(self) -> None:
        """Update confidence band."""
        if self.props.fit_result is None:
            return
        self._update_confidence_band()
        self.set_results(Graphs.CurveFittingError.NONE)
        self.update_canvas_data()

    def _update_confidence_band(self) -> None:
        """Calculate and update confidence band for error propagation."""
        if self.props.fit_result is None:
            return

        conf_level = self.get_settings().get_enum("confidence")
        x_min, x_max = self._xlim
        x_values, y_values = utilities.equation_to_data(
            self.fitted_curve.equation, (x_min, x_max))
        x_values = numpy.asarray(x_values)

        eq_str = self.get_equation_string()
        param_names = self.props.fitting_parameters.get_free_vars()

        sym_x = sympy.Symbol("x", real=True)
        sym_params_map = \
            {name: sympy.Symbol(name, real=True) for name in param_names}
        sym_params_list = [sym_params_map[name] for name in param_names]
        sym_params_map["x"] = sym_x
        expr = sympy.sympify(eq_str, locals=sym_params_map)

        parameters = self.props.fit_result.get_parameters()
        n_points = x_values.size
        n_params = len(parameters)
        jacobian = numpy.zeros((n_points, n_params))

        for i, name in enumerate(param_names):
            deriv = sympy.diff(expr, sym_params_map[name])
            f_deriv = sympy.lambdify([sym_x, *sym_params_list], deriv, "numpy")
            jacobian[:, i] = f_deriv(x_values, *parameters)

        variance = numpy.sum((jacobian @ self._covariance)
                             * jacobian,
                             axis=1)

        std_dev_y = numpy.sqrt(numpy.abs(variance))
        confidence_band = std_dev_y * conf_level

        y_upper = y_values + confidence_band
        y_lower = y_values - confidence_band
        self.fill.props.data = (x_values, y_lower, y_upper)

    def _clear_fit(self) -> None:
        """Clear all fit-related data by hiding curves."""
        self.props.fit_result = None
        self._update_residuals()
        # Hide fitted curve and fill by hiding their matplotlib artists
        cv = self.get_canvas()

        if cv:
            # Hide all lines except the first one (data curve)
            for line in cv.figure.axis.lines[1:]:
                line.set_visible(False)
            # Hide all collections (fill)
            for collection in cv.figure.axis.collections:
                collection.set_visible(False)
            cv.queue_draw()

    def _display_fit_results(self) -> None:
        """Display the fitting results in the text buffer."""
        if self.props.fit_result is None:
            return

        buffer = self.get_text_view().get_buffer()
        buffer.insert_with_tags_by_name(
            buffer.get_end_iter(),
            f"{_('Parameters')}\n",
            "bold",
        )

        free_vars = self.props.fitting_parameters.get_free_vars()
        diag_covars = self.props.fit_result.get_diag_covars()
        params = self.props.fit_result.get_parameters()
        conf_level = self.get_settings().get_enum("confidence")

        for var, diag_cov, param in zip(free_vars, diag_covars, params):
            line = f"{var}: {param:.3g}"
            if conf_level > 0:
                err = f"{diag_cov * conf_level:.3g}"
                line += f" (± {err})"
            buffer.insert(buffer.get_end_iter(), f"{line}\n")

        buffer.insert(buffer.get_end_iter(), "\n")
        buffer.insert_with_tags_by_name(
            buffer.get_end_iter(),
            f"{_('Statistics')}\n",
            "bold",
        )

        r2, rmse = self.props.fit_result.get_r2_rmse()

        buffer.insert(
            buffer.get_end_iter(),
            f"{_('R²')}: {r2}\n",
        )
        buffer.insert(
            buffer.get_end_iter(),
            f"{_('RMSE')}: {rmse}",
        )

    def _add_fit(self) -> None:
        """Add fitted data to the items in the main application."""
        self.props.window.get_data().add_items([self.fitted_curve])
