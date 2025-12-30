# SPDX-License-Identifier: GPL-3.0-or-later
"""Curve fitting module."""
import re
from gettext import gettext as _

from gi.repository import Adw, Gio, Graphs

from graphs import utilities
from graphs.canvas import Canvas
from graphs.item import DataItem, EquationItem, FillItem

import numpy

from scipy.optimize import _minpack, curve_fit

import sympy


# Constants
DATA_COLOR = "#1A5FB4"
FIT_COLOR = "#A51D2D"
FILL_ALPHA = 0.15
MARKER_STYLE = 1
MARKER_SIZE = 13
LINE_STYLE = 0


class CurveFittingDialog(Graphs.CurveFittingDialog):
    """Class for displaying the Curve Fitting dialog."""

    __gtype_name__ = "GraphsPythonCurveFittingDialog"

    def __init__(self, window: Graphs.Window, item: Graphs.Item):
        """Initialize the curve fitting dialog."""
        super().__init__(window=window)
        application = window.get_application()
        Adw.StyleManager.get_default().connect("notify", self.reload_canvas)
        self.connect("equation-change", self.on_equation_change)
        self.connect("fit-curve-request", self.fit_curve)
        self.connect("add-fit-request", self.add_fit)
        self.fitting_parameters = FittingParameterContainer()
        style = \
            application.get_figure_style_manager().get_system_style_params()

        self.param = []
        self.param_cov = []
        self.r2 = 0
        self.rmse = 0

        # Generate items for the canvas
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
            color=DATA_COLOR,
            alpha=FILL_ALPHA,
        )

        self._items = Gio.ListStore.new(Graphs.Item)
        self._items.append(self.data_curve)

        self.reload_canvas()
        self.setup()
        self.present(window)

    def reload_canvas(self, *_args) -> None:
        """Reinitialise the currently used canvas."""
        style_manager = \
            self.props.window.get_application().get_figure_style_manager()
        style = style_manager.get_system_style_params()
        figure_settings = self.props.window.get_data().get_figure_settings()

        canvas = Canvas(style, self._items, interactive=False)
        ax = canvas.figure.axes[0]
        ax.yscale = ax.xscale = "linear"
        ax.xlabel = _("X Value")

        if self.get_canvas():
            ax.set_xlim(self.get_canvas().figure.axes[0].get_xlim())

        canvas.left_label = figure_settings.get_property("left_label")
        canvas.bottom_label = figure_settings.get_property("bottom_label")
        self.set_canvas(canvas)

    @staticmethod
    def on_equation_change(self, equation: str) -> bool:
        """Handle equation changes and update fitting parameters."""
        processed_eq = utilities.preprocess(equation)
        self.set_equation_string(processed_eq)
        free_vars = utilities.get_free_variables(processed_eq)

        if not free_vars:
            self.set_results(error="equation")
            return False

        self.fitting_parameters.update(free_vars)

        box = self.get_fitting_params_box()
        while box.get_last_child() is not None:
            box.remove(box.get_last_child())

        use_bounds = self.get_settings().get_string("optimization") != "lm"
        for param in self.fitting_parameters:
            p_box = Graphs.FittingParameterBox.new(param)
            p_box.set_bounds_visible(use_bounds)
            for prop in ["initial", "upper_bound", "lower_bound"]:
                p_box.get_property(prop).connect(
                    "notify::text",
                    self.on_entry_change)
            box.append(p_box)

        return True

    def on_entry_change(self, entry, _param) -> None:
        """Validate and update fitting parameter bounds on user input."""
        target_row = entry.get_ancestor(Graphs.FittingParameterBox)
        if not target_row:
            return

        fitting_box = self.get_fitting_params_box()
        for row, params in zip(fitting_box, self.fitting_parameters):
            if row != target_row:
                continue

            widgets = {
                "init": row.get_initial(),
                "low": row.get_lower_bound(),
                "high": row.get_upper_bound()}
            for w in widgets.values():
                w.remove_css_class("error")

            try:
                vals = {k: float(w.get_text()) for k, w in widgets.items()}

                if not (vals["low"] <= vals["init"] <= vals["high"]):
                    widgets["init"].add_css_class("error")
                    error = True
                if vals["low"] >= vals["high"]:
                    widgets["low"].add_css_class("error")
                    widgets["high"].add_css_class("error")
                    error = True

                if error:
                    self.set_results(error="bounds")
                    return

                params.set_initial(vals["init"])
                params.set_lower_bound(str(vals["low"]))
                params.set_upper_bound(str(vals["high"]))

            except ValueError:
                entry.add_css_class("error")
                self.set_results(error="value")
                return

        if not error:
            self.fit_curve()

    def fit_curve(self, *_args) -> bool:
        """Perform curve fitting and update results."""
        eq_str = self.get_equation_string()
        func = utilities.string_to_function(eq_str)
        if not func:
            self.set_results(error="equation")
            return False

        try:
            self.param, self.param_cov = curve_fit(
                func, self.data_curve.get_xdata(), self.data_curve.get_ydata(),
                p0=self.fitting_parameters.get_p0(),
                bounds=self.fitting_parameters.get_bounds(),
                nan_policy="omit",
                method=self.get_settings().get_string("optimization"),
            )

            if numpy.any(numpy.isinf(self.param_cov)):
                self.set_results(error="singular")
                return False

        except RuntimeError:
            self.set_results(error="convergence")
            return False
        except (ValueError, TypeError):
            self.set_results(error="domain")
            return False
        except _minpack.error:
            self.set_results(error="convergence")
            return False
        except (ZeroDivisionError, OverflowError):
            self.set_results(error="domain")
            return False

        # Update visual equation name
        display_eq = str(self.get_custom_equation().get_text()).lower()
        free_vars = utilities.get_free_variables(eq_str)
        for i, var in enumerate(free_vars):
            val = utilities.sig_fig_round(self.param[i], 3)
            display_eq = re.sub(rf"\b{var}\b", f"({val})", display_eq)

        self.fitted_curve.equation = display_eq
        self.fitted_curve.set_name(f"Y = {display_eq}")

        self.reload_canvas()
        self.set_r2(func)
        self.get_confidence()
        self.set_results()
        return True

    def set_results(self, error="") -> None:
        """Display fitting results or error message in the results view."""
        buffer = self.get_text_view().get_buffer()

        error_messages = {
            "value": _("Please enter valid \nnumeric parameters."),
            "bounds": _(
                "Constraint error: ensure \nLower < Initial < Upper."),
            "singular": _(
                "Matrix error: Data is \ninsufficient for this model."),
            "convergence": _(
                "Fit failed: Max iterations \nreached without converging."),
            "domain": _(
                "Domain error: Equation not \nvalid for this data range."),
            "equation": _(
                "Invalid equation: Check \nsyntax and variables."),
        }

        if error:
            buffer.set_text(f"{_('Results:')}\n{error_messages[error]}")
            self._items.remove_all()
            self._items.append(self.data_curve)
            self.reload_canvas()
        else:
            self._items.remove_all()
            self._items.append(self.fitted_curve)
            self._items.append(self.fill)
            self._items.append(self.data_curve)

            free_vars = utilities.get_free_variables(
                self.get_equation_string())
            lines = [_("Results:")]
            diag_cov = numpy.sqrt(numpy.diagonal(self.param_cov))
            conf_level = self.get_settings().get_enum("confidence")

            for i, var in enumerate(free_vars):
                val = utilities.sig_fig_round(self.param[i], 3)
                line = f"{var}: {val}"
                if conf_level > 0:
                    err = utilities.sig_fig_round(diag_cov[i] * conf_level, 3)
                    line += f" (± {err})"
                lines.append(line)

            lines.append(f"\n{_('R²')}: {self.r2}")
            lines.append(f"{_('RMSE')}: {self.rmse}")
            buffer.set_text("\n".join(lines))
            self.reload_canvas()

        # Style the first word (Results:)
        start = buffer.get_start_iter()
        end = buffer.get_start_iter()
        end.forward_to_line_end()
        tag = buffer.get_tag_table().lookup("bold")
        if not tag:
            tag = buffer.create_tag("bold", weight=700)
        buffer.apply_tag(tag, start, end)

    def set_r2(self, func) -> None:
        """Calculate the r2 coefficient for the fit."""
        x_data = numpy.asarray(self.data_curve.get_xdata())
        y_data = numpy.asarray(self.data_curve.get_ydata())
        fitted_y = func(x_data, *self.param)

        ss_res = numpy.sum((y_data - fitted_y)**2)
        ss_tot = numpy.sum((y_data - numpy.mean(y_data))**2)

        self.r2 = utilities.sig_fig_round(1 - (ss_res / ss_tot), 3)
        n = len(y_data)
        self.rmse = utilities.sig_fig_round(numpy.sqrt(ss_res / n), 3)

    def get_confidence(self) -> None:
        """Calculate and plot confidence band for error propagation.

        Uses the Delta Method: var_y = diag(Jacobian @ covar @ Jacobian.T)
        """
        conf_level = self.get_settings().get_enum("confidence")
        if conf_level == 0:
            self.fill.props.data = (
                numpy.array([]),
                numpy.array([]),
                numpy.array([]))
            return

        ax = self.get_canvas().figure.axes[0]
        x_limits = ax.get_xlim()
        x_values, y_values = utilities.equation_to_data(
            self.fitted_curve.equation, x_limits)
        x_values = numpy.asarray(x_values)

        eq_str = self.get_equation_string()
        param_names = utilities.get_free_variables(eq_str)

        # Define Symbols
        sym_x = sympy.Symbol("x")
        sym_params_map = {name: sympy.Symbol(name) for name in param_names}
        sym_params_list = [sym_params_map[name] for name in param_names]
        sym_params_map["x"] = sym_x
        expr = sympy.sympify(eq_str, locals=sym_params_map)

        # Compute Jacobian
        n_points = x_values.size
        n_params = len(self.param)
        jacobian = numpy.zeros((n_points, n_params))

        for i, name in enumerate(param_names):
            deriv_expr = sympy.diff(expr, sym_params_map[name])
            calculate_deriv = sympy.lambdify(
                [sym_x] + sym_params_list, deriv_expr, modules="numpy")
            d_vals = calculate_deriv(x_values, *self.param)
            jacobian[:, i] = numpy.full(n_points, d_vals) \
                if numpy.isscalar(d_vals) else d_vals

        variance = numpy.sum((jacobian @ self.param_cov) * jacobian, axis=1)
        std_dev_y = numpy.sqrt(numpy.maximum(variance, 0))

        confidence_band = std_dev_y * conf_level

        y_upper = y_values + confidence_band
        y_lower = y_values - confidence_band

        self.fill.props.data = (x_values, y_lower, y_upper)

    @staticmethod
    def add_fit(self) -> None:
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

    def update(self, parameters: list) -> None:
        """Update parameters with new values."""
        new_items = {}
        for var in parameters:
            new_items[var] = self._items.get(
                var,
                Graphs.FittingParameter(
                    name=var,
                    initial=1.0,
                    lower_bound="-inf",
                    upper_bound="inf",
                ))
        self._items = new_items

    def get_p0(self) -> list:
        """Get the initial values of the fitting."""
        return [float(item_.get_initial()) for item_ in self]

    def get_bounds(self) -> tuple:
        """Get the bounds of the fitting parameters."""
        lower_bounds = [float(item_.get_lower_bound()) for item_ in self]
        upper_bounds = [float(item_.get_upper_bound()) for item_ in self]
        return (lower_bounds, upper_bounds)
