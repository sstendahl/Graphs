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


class FitResult:
    """Container for curve fitting results."""

    def __init__(self, parameters, covariance, r2, rmse, residuals, fitted_y):
        self.parameters = parameters
        self.covariance = covariance
        self.r2 = r2
        self.rmse = rmse
        self.residuals = residuals
        self.fitted_y = fitted_y

    @property
    def is_valid(self):
        """Check whether the fit result has a valid variance."""
        nonfinite_covariance = numpy.any(numpy.isinf(self.covariance))
        return len(self.parameters) > 0 and not nonfinite_covariance


class CurveFittingDialog(Graphs.CurveFittingDialog):
    """Class for displaying the Curve Fitting dialog."""

    __gtype_name__ = "GraphsPythonCurveFittingDialog"

    def __init__(self, window: Graphs.Window, item: Graphs.Item):
        """Initialize the curve fitting dialog."""
        super().__init__(window=window)
        self.connect("equation-change", self.on_equation_change)
        self.connect("fit-curve-request", self.on_fit_curve_request)
        self.connect("add-fit-request", self.add_fit)
        self.connect("show-residuals-changed", self.load_residuals_canvas)
        self.connect("update-confidence-request", self.update_confidence_band)
        Adw.StyleManager.get_default().connect("notify", self.load_canvas)

        self.fitting_parameters = FittingParameterContainer()
        self.fit_result = None

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
        )
        self.residuals_item.linestyle = LINE_STYLE
        self.residuals_item.markerstyle = MARKER_STYLE
        self.residuals_item.markersize = MARKER_SIZE
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
        self.load_residuals_canvas()
        if self.get_error():
            self._clear_fit()

    def load_residuals_canvas(self, *_args):
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

    def on_equation_change(self, _sender, equation: str) -> bool:
        """Handle equation changes and update parameters."""
        try:
            processed_eq = Graphs.preprocess_equation(equation)
            free_vars = set(Graphs.math_tools_get_free_variables(processed_eq))
        except GLib.Error:
            return False
        if not free_vars:
            self._clear_fit()
            self.set_results(error="equation")
            return False

        self.set_equation_string(processed_eq)
        self._update_parameter_widgets(free_vars)
        if self.fit_result is not None:
            self._update_residuals()
        return True

    def _update_parameter_widgets(self, free_vars: set) -> None:
        """Update parameter widgets when equation changes."""
        current_params = set(self.fitting_parameters._items.keys())
        if current_params == free_vars:
            return

        self.fitting_parameters.update(free_vars)
        box = self.get_fitting_params_box()

        # Clear existing widgets
        while box.get_last_child():
            box.remove(box.get_last_child())

        # Create new parameter boxes
        use_bounds = self.get_settings().get_string("optimization") != "lm"
        for param in self.fitting_parameters:
            p_box = Graphs.FittingParameterBox.new(param)
            p_box.set_bounds_visible(use_bounds)

            for prop in ("initial", "upper_bound", "lower_bound"):
                p_box.get_property(prop).connect(
                    "notify::text",
                    self.on_entry_change,
                )
            box.append(p_box)

    def on_entry_change(self, entry, _param) -> None:
        """Validate and update fitting parameter bounds on user input."""
        target_row = entry.get_ancestor(Graphs.FittingParameterBox)
        fitting_box = self.get_fitting_params_box()

        for row, params in zip(fitting_box, self.fitting_parameters):
            if row != target_row:
                continue

            if not self._validate_and_update_parameter(row, params):
                return

        # Only refit if all parameters are valid
        self.on_fit_curve_request()

    def _validate_and_update_parameter(self, row, params) -> bool:
        """Validate a single parameter row and update if valid."""
        widgets = {
            "init": row.get_initial(),
            "low": row.get_lower_bound(),
            "high": row.get_upper_bound(),
        }

        vals = {}
        value_error = False
        for key, widget in widgets.items():
            try:
                vals[key] = Graphs.evaluate_string(widget.get_text())
                widget.remove_css_class("error")
            except GLib.Error:
                widget.add_css_class("error")
                value_error = True

        if value_error:
            self.set_results(error="value")
            return False

        if vals["low"] >= vals["high"]:
            widgets["low"].add_css_class("error")
            widgets["high"].add_css_class("error")
            self.set_results(error="bounds")
            return False

        if not (vals["low"] <= vals["init"] <= vals["high"]):
            widgets["init"].add_css_class("error")
            self.set_results(error="bounds")
            return False

        params.set_initial(vals["init"])
        params.set_lower_bound(vals["low"])
        params.set_upper_bound(vals["high"])
        return True

    def on_fit_curve_request(self, *_args) -> None:
        """Handle fit curve request."""
        if not self.get_equation_string():
            self.set_results(error="equation")
            return

        fit_result = self._perform_fit()

        if fit_result is None:
            return
        self.fit_result = fit_result

        # Update all UI components
        self._update_fitted_curve()
        self._update_residuals()
        self._update_confidence_band()
        self.update_canvas_data()
        self.set_results()

    def _get_function(self) -> sympy.FunctionClass:
        variables = ["x"] + list(self.fitting_parameters.parameters)
        sym_vars = sympy.symbols(variables)
        with contextlib.suppress(sympy.SympifyError, TypeError, SyntaxError):
            symbolic = sympy.sympify(
                self.get_equation_string(),
                locals=dict(zip(variables, sym_vars)),
            )
            return sympy.lambdify(sym_vars, symbolic)

    def _perform_fit(self) -> FitResult:
        """Perform the actual curve fitting."""
        func = self._get_function()
        if not func:
            self.set_results(error="equation")
            return None

        x_data = numpy.asarray(self.data_curve.get_xdata())
        y_data = numpy.asarray(self.data_curve.get_ydata())

        try:
            params, param_cov = curve_fit(
                func, x_data, y_data,
                p0=self.fitting_parameters.get_p0(),
                bounds=self.fitting_parameters.get_bounds(),
                nan_policy="omit",
                method=self.get_settings().get_string("optimization"),
            )

            if numpy.any(numpy.isinf(param_cov)):
                self.set_results(error="singular")
                return None

        except RuntimeError:
            self.set_results(error="convergence")
            return None
        except (ValueError, TypeError):
            self.set_results(error="domain")
            return None
        except _minpack.error:
            self.set_results(error="convergence")
            return None
        except (ZeroDivisionError, OverflowError):
            self.set_results(error="domain")
            return None

        # Calculate statistics
        fitted_y = func(x_data, *params)
        residuals = y_data - fitted_y
        r2, rmse = self._calculate_statistics(y_data, fitted_y)

        return FitResult(params, param_cov, r2, rmse, residuals, fitted_y)

    def _calculate_statistics(
        self,
        y_data: numpy.ndarray,
        fitted_y: numpy.ndarray,
    ) -> tuple:
        """Calculate R² and RMSE statistics."""
        ss_res = numpy.sum((y_data - fitted_y)**2)
        ss_tot = numpy.sum((y_data - numpy.mean(y_data))**2)
        r2 = 1 - (ss_res / ss_tot)

        n = len(y_data)
        rmse = numpy.sqrt(ss_res / n)

        return f"{r2:.3g}", f"{rmse:.3g}"

    def _update_fitted_curve(self) -> None:
        """Update the fitted curve on the main canvas."""
        equation = self.get_equation_string()
        eq_name = equation.lower()

        # Substitute each free variables with the calculated value.
        free_vars = self.fitting_parameters.parameters
        params = self.fit_result.parameters
        for var, param_value in zip(free_vars, params):
            var_pattern = rf"\b{re.escape(var)}\b"
            equation = re.sub(var_pattern, f"({param_value})", equation)
            rounded = f"{param_value:.3g}"
            eq_name = re.sub(var_pattern, f"{rounded}", eq_name)

        eq_name = Graphs.prettify_equation(eq_name)

        # Clean up combined operators
        eq_name = (
            eq_name.replace("--", "+").replace("+-", "-").replace("-+", "-")
        )
        # Remove + signs at the start, or after an opening +
        eq_name = re.sub(
            r"""
            (^|\()   # Group 1: Look for either the start of the line OR a "("
            \+       # Look for a "+" immediately after it
            """,
            r"\1",  # Put back only group 1 without the +
            eq_name,
            flags=re.VERBOSE,
        )

        self.fitted_curve.equation = equation
        self.fitted_curve.set_name(f"Y = {eq_name}")

        # Show fill and fit again after successful fit
        cv = self.get_canvas()
        if self.get_error() and cv:
            for line in cv.figure.axis.lines[1:]:
                line.set_visible(True)
            for collection in cv.figure.axis.collections:
                collection.set_visible(True)
            self.set_error(False)
            self._update_residuals()
            self.load_canvas()

    def _update_residuals(self) -> None:
        """Update residuals plot."""
        xdata = numpy.asarray(self.data_curve.get_xdata())
        if self.fit_result is None:
            residuals = numpy.zeros(len(self.data_curve.get_xdata()))
        else:
            residuals = self.fit_result.residuals
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

    def update_confidence_band(self, *_args) -> None:
        """Update confidence band."""
        if self.fit_result is None or not self.fit_result.is_valid:
            return
        self._update_confidence_band()
        self.set_results()
        self.update_canvas_data()

    def _update_confidence_band(self) -> None:
        """Calculate and update confidence band for error propagation."""
        if self.fit_result is None:
            return

        conf_level = self.get_settings().get_enum("confidence")
        x_min, x_max = self._xlim
        x_values, y_values = utilities.equation_to_data(
            self.fitted_curve.equation, (x_min, x_max))
        x_values = numpy.asarray(x_values)

        eq_str = self.get_equation_string()
        param_names = self.fitting_parameters.parameters

        sym_x = sympy.Symbol("x", real=True)
        sym_params_map = \
            {name: sympy.Symbol(name, real=True) for name in param_names}
        sym_params_list = [sym_params_map[name] for name in param_names]
        sym_params_map["x"] = sym_x
        expr = sympy.sympify(eq_str, locals=sym_params_map)

        n_points = x_values.size
        n_params = len(self.fit_result.parameters)
        jacobian = numpy.zeros((n_points, n_params))

        for i, name in enumerate(param_names):
            deriv = sympy.diff(expr, sym_params_map[name])
            f_deriv = sympy.lambdify([sym_x, *sym_params_list], deriv, "numpy")
            jacobian[:, i] = f_deriv(x_values, *self.fit_result.parameters)

        variance = numpy.sum((jacobian @ self.fit_result.covariance)
                             * jacobian,
                             axis=1)

        std_dev_y = numpy.sqrt(numpy.abs(variance))
        confidence_band = std_dev_y * conf_level

        y_upper = y_values + confidence_band
        y_lower = y_values - confidence_band
        self.fill.props.data = (x_values, y_lower, y_upper)

    def _clear_fit(self) -> None:
        """Clear all fit-related data by hiding curves."""
        self.fit_result = None
        self.set_error(True)
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

    def set_results(self, error="") -> None:
        """Display fitting results or error message in the results view."""
        view = self.get_text_view()
        buffer = view.get_buffer()
        buffer.set_text("")
        tag_table = buffer.get_tag_table()
        bold_tag = tag_table.lookup("bold")
        if not bold_tag:
            bold_tag = buffer.create_tag("bold", weight=700)
        error_messages = {
            "value":
            _("Please enter valid \nnumeric parameters."),
            "bounds":
            _("Constraint error: ensure \nLower < Initial < Upper."),
            "singular":
            _("Matrix error: Data is \ninsufficient for this model."),
            "convergence":
            _("Fit failed: Max iterations \nreached without converging."),
            "domain":
            _("Domain error: Equation not \nvalid for this data range."),
            "equation":
            _("Invalid equation: Check \nsyntax and variables."),
            "confidence":
            _("Confidence band error: \nCovariance matrix is unstable."),
        }

        if error:
            buffer.insert(buffer.get_end_iter(), error_messages[error])
            self._clear_fit()
        else:
            if self.fit_result is None or not self.fit_result.is_valid:
                return

            self._display_fit_results(buffer)

    def _display_fit_results(self, buffer) -> None:
        """Display the fitting results in the text buffer."""
        buffer.insert_with_tags_by_name(
            buffer.get_end_iter(),
            f"{_('Parameters')}\n",
            "bold",
        )

        free_vars = self.fitting_parameters.parameters
        diag_covars = numpy.sqrt(numpy.diagonal(self.fit_result.covariance))
        params = self.fit_result.parameters
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

        buffer.insert(
            buffer.get_end_iter(),
            f"{_('R²')}: {self.fit_result.r2}\n",
        )
        buffer.insert(
            buffer.get_end_iter(),
            f"{_('RMSE')}: {self.fit_result.rmse}",
        )

    def add_fit(self, _parent) -> None:
        """Add fitted data to the items in the main application."""
        self.props.window.get_data().add_items([self.fitted_curve])
        self.close()


class FittingParameterContainer:
    """Container for managing fitting parameters."""

    def __init__(self):
        """Initialize the container."""
        self._items = {}

    def __iter__(self):
        """Iterate over items."""
        return iter(self._items.values())

    def update(self, parameters: set) -> None:
        """Update parameters with new values."""
        self.parameters = parameters
        self._items = {
            var: self._items.get(var, Graphs.FittingParameter.new(var))
            for var in parameters
        }

    def get_p0(self) -> list:
        """Get the initial values of the fitting."""
        return [float(item_.get_initial()) for item_ in self]

    def get_bounds(self) -> tuple:
        """Get the bounds of the fitting parameters."""
        lower_bounds = [item_.get_lower_bound() for item_ in self]
        upper_bounds = [item_.get_upper_bound() for item_ in self]
        return (lower_bounds, upper_bounds)
