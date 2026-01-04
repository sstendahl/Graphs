# SPDX-License-Identifier: GPL-3.0-or-later
"""Curve fitting module."""
import re
from gettext import gettext as _

from gi.repository import Adw, Gio, Graphs

from graphs import canvas, utilities
from graphs.item import DataItem, EquationItem, FillItem

import numpy

from scipy.optimize import _minpack, curve_fit

import sympy


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
        self.connect("equation-change", self.on_equation_change)
        self.connect("fit-curve-request", self.fit_curve)
        self.connect("add-fit-request", self.add_fit)
        self.connect("show-residuals-changed", self.reload_residuals_canvas)
        Adw.StyleManager.get_default().connect("notify", self.load_canvas)
        app = window.get_application()
        style = app.get_figure_style_manager().get_system_style_params()

        self.fitting_parameters = FittingParameterContainer()
        self.param = []
        self.param_cov = []
        self.r2 = 0
        self.rmse = 0

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

        self._residuals_items = Gio.ListStore.new(Graphs.Item)

        x_data = numpy.asarray(self.data_curve.get_xdata())
        x_min, x_max = x_data.min(), x_data.max()
        x_range = x_max - x_min
        padding = x_range * 0.025
        self._xlim = (x_min - padding, x_max + padding)

        self.setup()
        self.present(window)
        self.load_canvas()

    def load_canvas(self, *_args) -> None:
        """Initialize canvases once during dialog creation."""
        window_data = self.props.window.get_data()
        settings = window_data.get_figure_settings()
        app = self.props.window.get_application()
        style = app.get_figure_style_manager().get_system_style_params()

        cv = canvas.Canvas(style, self._items, interactive=False)
        ax = cv.figure.axis
        ax.set(xlabel=settings.get_property("bottom_label"),
               ylabel=settings.get_property("left_label"),
               xlim=self._xlim,
               )

        self.reload_residuals_canvas()
        self.set_canvas(cv)

    def update_canvas_data(self):
        """Recreate canvas to properly update all items including fill."""
        app = self.props.window.get_application()
        style = app.get_figure_style_manager().get_system_style_params()
        settings = self.props.window.get_data().get_figure_settings()

        cv = canvas.Canvas(style, self._items, interactive=False)
        ax = cv.figure.axis
        ax.set_xlabel(settings.get_property("bottom_label"))
        ax.set_ylabel(settings.get_property("left_label"))
        ax.set_xlim(*self._xlim)

        if self.fitted_curve in self._items:
            equation = self.fitted_curve.equation
            x_values, y_values = \
                utilities.equation_to_data(equation, self._xlim)
            current_lim = ax.get_ylim()
            y_values.extend(current_lim)
            y_min, y_max = min(y_values), max(y_values)
            y_range = y_max - y_min
            if y_range > 0:
                y_padding = y_range * 0.025
                ax.set_ylim(y_min - y_padding, y_max + y_padding)
        self.set_canvas(cv)

    def reload_residuals_canvas(self, *_args):
        """Create or update the residuals canvas."""
        if not self.get_settings().get_boolean("show-residuals"):
            self.set_residuals_canvas(None)
            return
        app = self.props.window.get_application()
        style = app.get_figure_style_manager().get_system_style_params()
        settings = self.props.window.get_data().get_figure_settings()

        res_cv = canvas.Canvas(style, self._residuals_items, interactive=False)
        res_ax = res_cv.figure.axis
        res_ax.get_legend().remove()
        res_ax.set_ylabel(_("Residuals"))
        res_ax.set_xlabel(settings.get_property("bottom_label"))
        res_ax.axhline(y=0, color="black", linestyle="--", linewidth=0.5)
        res_ax.set_xlim(*self._xlim)
        if res_ax.get_legend():
            res_ax.get_legend().remove()

        res_y = numpy.asarray(self._residuals_items[0].get_ydata())
        if res_y.size > 0:
            max_val = abs(res_y).max()
            if max_val > 0:
                res_pad = max_val * 1.1
                res_ax.set_ylim(-res_pad, res_pad)

        self.set_residuals_canvas(res_cv)

    @staticmethod
    def on_equation_change(self, equation: str) -> bool:
        """Handle equation changes and update fitting parameters."""
        processed_eq = utilities.preprocess(equation)
        self.set_equation_string(processed_eq)
        free_vars = utilities.get_free_variables(processed_eq)

        if not free_vars:
            self.set_results(error="equation")
            return False

        # Only update parameters if they've actually changed
        current_params = set(self.fitting_parameters._items.keys())
        if current_params != set(free_vars):
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
        error = False
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

        display_eq = str(self.get_custom_equation().get_text()).lower()
        free_vars = utilities.get_free_variables(eq_str)
        for i, var in enumerate(free_vars):
            val = utilities.sig_fig_round(self.param[i], 3)
            display_eq = re.sub(rf"\b{var}\b", f"({val})", display_eq)

        self.fitted_curve.equation = display_eq
        self.fitted_curve.set_name(f"Y = {display_eq}")

        x_data = numpy.asarray(self.data_curve.get_xdata())
        y_data = numpy.asarray(self.data_curve.get_ydata())
        self._update_residuals(func, x_data, y_data)
        self.set_r2(func)
        self.get_confidence()
        self.set_results()

        return True

    def _update_residuals(self, func: callable, x_data: numpy.ndarray,
                          y_data: numpy.ndarray) -> None:
        """Calculate and update residuals."""
        fitted_y = func(x_data, *self.param)
        residuals = y_data - fitted_y

        app = self.props.window.get_application()
        style = app.get_figure_style_manager().get_system_style_params()
        residuals_item = DataItem.new(
            style,
            xdata=x_data.tolist(),
            ydata=residuals.tolist(),
            color=DATA_COLOR,
            name="",
        )

        residuals_item.linestyle = LINE_STYLE
        residuals_item.markerstyle = MARKER_STYLE
        residuals_item.markersize = MARKER_SIZE

        self._residuals_items.remove_all()
        self._residuals_items.append(residuals_item)

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
            "confidence": _(
                "Confidence band error: \nCovariance matrix is unstable."),
        }

        if error:
            buffer.insert(buffer.get_end_iter(), error_messages[error])
            self._items.remove_all()
            self._items.append(self.data_curve)
            self._residuals_items.remove_all()
        else:
            if len(self.param) == 0 or not self.get_equation_string():
                return

            self._items.remove_all()
            self._items.append(self.fitted_curve)
            self._items.append(self.fill)
            self._items.append(self.data_curve)

            buffer.insert_with_tags_by_name(
                buffer.get_end_iter(), f"{_('Parameters')}\n", "bold")
            free_vars = utilities.get_free_variables(
                self.get_equation_string())
            diag_cov = numpy.sqrt(numpy.diagonal(self.param_cov))
            conf_level = self.get_settings().get_enum("confidence")

            for i, var in enumerate(free_vars):
                val = utilities.sig_fig_round(self.param[i], 3)
                line = f"{var}: {val}"
                if conf_level > 0:
                    err = utilities.sig_fig_round(diag_cov[i] * conf_level, 3)
                    line += f" (± {err})"
                buffer.insert(buffer.get_end_iter(), f"{line}\n")

            buffer.insert(buffer.get_end_iter(), "\n")
            buffer.insert_with_tags_by_name(
                buffer.get_end_iter(), f"{_('Statistics')}\n", "bold")

            buffer.insert(buffer.get_end_iter(), f"{_('R²')}: {self.r2}\n")
            buffer.insert(buffer.get_end_iter(), f"{_('RMSE')}: {self.rmse}")
        self.update_canvas_data()

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
        """Calculate and plot confidence band for error propagation."""
        conf_level = self.get_settings().get_enum("confidence")
        if conf_level == 0:
            self.fill.props.data = (
                numpy.array([]),
                numpy.array([]),
                numpy.array([]),
            )
            return

        x_min, x_max = self._xlim
        x_values, y_values = utilities.equation_to_data(
            self.fitted_curve.equation, (x_min, x_max))
        x_values = numpy.asarray(x_values)
        eq_str = self.get_equation_string()
        param_names = utilities.get_free_variables(eq_str)

        sym_x = sympy.Symbol("x", real=True)
        sym_params_map = \
            {name: sympy.Symbol(name, real=True) for name in param_names}
        sym_params_list = [sym_params_map[name] for name in param_names]
        sym_params_map["x"] = sym_x
        expr = sympy.sympify(eq_str, locals=sym_params_map)

        n_points = x_values.size
        n_params = len(self.param)
        jacobian = numpy.zeros((n_points, n_params))

        for i, name in enumerate(param_names):
            deriv = sympy.diff(expr, sym_params_map[name])
            f_deriv = sympy.lambdify([sym_x, *sym_params_list], deriv, "numpy")
            jacobian[:, i] = f_deriv(x_values, *self.param)

        variance = numpy.sum((jacobian @ self.param_cov) * jacobian, axis=1)

        if numpy.any(variance < -1e-10):
            self.fill.props.data = (
                numpy.array([]),
                numpy.array([]),
                numpy.array([]),
            )
            self.set_results(error="confidence")
            return

        std_dev_y = numpy.sqrt(numpy.abs(variance))
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
