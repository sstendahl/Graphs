# SPDX-License-Identifier: GPL-3.0-or-later
import re
from gettext import gettext as _

from gi.repository import Adw, GObject, Gio, Graphs, Gtk

from graphs import ui, utilities
from graphs.canvas import Canvas
from graphs.data import Data
from graphs.item import DataItem, FillItem
from graphs.misc import EQUATIONS

import numpy

from scipy.optimize import _minpack, curve_fit


class CurveFittingWindow(Graphs.CurveFittingTool):
    __gtype_name__ = "GraphsCurveFittingWindow"
    confirm_button = GObject.Property(type=Gtk.Button)
    custom_equation = GObject.Property(type=Adw.EntryRow)
    equation = GObject.Property(type=Adw.ComboRow)
    fitting_params = GObject.Property(type=Gtk.Box)
    text_view = GObject.Property(type=Gtk.TextView)
    title_widget = GObject.Property(type=Adw.WindowTitle)
    toast_overlay = GObject.Property(type=Adw.ToastOverlay)

    def __init__(self, application, item):
        """Initialize the curve fitting dialog"""
        super().__init__(
            application=application, transient_for=application.get_window(),
        )
        Adw.StyleManager.get_default().connect("notify", self.reload_canvas)
        self.settings = \
            self.get_application().get_settings_child("curve-fitting")
        self.custom_equation = self.get_custom_equation()
        self.equation = self.get_equation()
        ignorelist = ["optimization", "confidence", "custom-equation"]
        ui.bind_values_to_settings(self.settings, self, ignorelist=ignorelist)
        self.custom_equation = self.get_custom_equation()
        self.set_equation()
        self.connect_actions()
        self.get_confirm_button().connect("clicked", self.add_fit)
        style = application.get_figure_style_manager(
        ).get_system_style_params()

        self.param = []
        self.sigma = []
        self.r2 = 0

        self.get_custom_equation().connect(
            "notify::text", self.on_equation_change)
        self.get_equation().connect(
            "notify::selected", self.set_equation)
        self.fitting_parameters = \
            FittingParameterContainer(application, application.get_settings())

        for var in self.get_free_variables():
            self.fitting_parameters.add_items([FittingParameter(name=var)])

        # Generate items for the canvas
        self.data_curve = DataItem.new(
            style, xdata=item.xdata, ydata=item.ydata,
            name=item.get_name(), color="#1A5FB4",
        )
        self.data_curve.linestyle = 0
        self.data_curve.markerstyle = 1
        self.data_curve.markersize = 13
        self.fitted_curve = DataItem.new(style, color="#A51D2D")
        self.fill = FillItem.new(
            style,
            (self.fitted_curve.xdata,
             self.fitted_curve.ydata, self.fitted_curve.ydata),
            color="#1A5FB4",
            alpha=0.15,
        )

        # Set up canvas
        self.reload_canvas()
        self.fit_curve()
        self.set_entry_rows()
        self.present()

    def connect_actions(self) -> None:
        """Connect the actions in the dialog to the action map"""
        action_map = Gio.SimpleActionGroup.new()
        self.insert_action_group("win", None)
        self.insert_action_group("win", action_map)
        for key in ["confidence", "optimization"]:
            action = self.settings.create_action(key)
            action.connect("notify", self.fit_curve)
            if key == "optimization":
                action.connect("notify", self._set_fitting_bounds_visibility)
            action_map.add_action(action)

    def set_equation(self, *_args) -> None:
        """Set the equation entry based on the current settings"""
        equation = EQUATIONS[self.settings.get_string("equation")]
        custom_equation = self.settings.get_string("custom-equation")
        if equation != "custom":
            self.equation.set_subtitle(f"Y={equation}")
            self.get_custom_equation().set_text(equation)
            self.get_custom_equation().set_visible(False)
        else:
            self.equation.set_subtitle("")
            self.get_custom_equation().set_text(custom_equation)
            self.get_custom_equation().set_visible(True)

    def _set_fitting_bounds_visibility(self, *_args):
        """Set the visibility of the fitting bounds"""
        for entry in self.get_fitting_params():
            entry.set_bounds_visibility()

    def reload_canvas(self, *_args):
        """Reinitialise the currently used canvas"""
        self.get_toast_overlay().set_child(None)
        figure_settings = self.get_application().get_data(
        ).get_figure_settings()
        style = self.get_application().get_figure_style_manager(
        ).get_system_style_params()
        canvas = Canvas(self.get_application(), style, interactive=False)
        canvas.props.items = [self.fitted_curve, self.data_curve, self.fill]
        axis = canvas.axes[0]
        axis.yscale = "linear"
        axis.xscale = "linear"
        axis.xlabel = "X Value"
        canvas.left_label = figure_settings.get_property("left_label")
        canvas.bottom_label = figure_settings.get_property("bottom_label")
        canvas.highlight_enabled = False
        canvas = canvas
        canvas._on_pan_gesture = None
        canvas._on_pick = None
        canvas.toolbar = None
        self.canvas = canvas
        self.get_toast_overlay().set_child(self.canvas)

    def get_free_variables(self) -> str:
        """Get a list of free variables in the equation entry"""
        pattern = (
            r"\b(?!x\b|X\b|csc\b|cot\b|sec\b|sin\b|cos\b|log\b|tan\b)"
            r"[a-wy-zA-WY-Z]+\b"
        )
        return re.findall(pattern, self.equation_string)

    def on_equation_change(self, _entry, _param):
        """
        Set the free variables and corresponding entry rows when the equation
        has been changed.
        """
        for var in self.get_free_variables():
            if var not in self.fitting_parameters.get_names():
                self.fitting_parameters.add_items([FittingParameter(name=var)])
        self.fitting_parameters.remove_unused(self.get_free_variables())
        fit = self.fit_curve()
        if fit:
            self.set_entry_rows()
            if self.settings.get_string("equation") == "custom":
                self.settings.set_string("custom-equation",
                                         self.equation_string)

    def on_entry_change(self, entry, _param):
        """
        Triggered whenever an entry changes. Update the parameters of the
        curve and perform a new subsequent fit.
        """
        error = False

        def _is_float(value):
            """
            Checks if a value can be converted to a float. If not, it adds a
            CSS class "error" to the entry.
            """
            try:
                float(value)
                return True
            except ValueError:
                entry.get_child().add_css_class("error")
                return False

        entries = entry.get_ancestor(FittingParameterEntry)
        # Set the parameters for the row corresponding to the entry that
        # was edited
        for row, params \
                in zip(self.get_fitting_params(), self.fitting_parameters):
            if row == entries:
                initial = entries.initial.get_text()
                lower_bound = entries.lower_bound.get_text()
                upper_bound = entries.upper_bound.get_text()
                entries.initial.get_child().remove_css_class("error")
                entries.lower_bound.get_child().remove_css_class("error")
                entries.upper_bound.get_child().remove_css_class("error")

                for bound in [initial, lower_bound, upper_bound]:
                    if not _is_float(bound):
                        self.set_results(error="value")
                        return

                initial = float(initial)
                lower_bound = float(lower_bound)
                upper_bound = float(upper_bound)

                if (initial < lower_bound
                        or initial > upper_bound):
                    entries.initial.get_child().add_css_class("error")
                    self.set_results(error="bounds")
                    error = True
                if not lower_bound < upper_bound:
                    entries.lower_bound.get_child().add_css_class("error")
                    entries.upper_bound.get_child().add_css_class("error")
                    error = True
                    self.set_results(error="bounds")

                params.set_initial(initial)
                params.set_lower_bound(str(lower_bound))
                params.set_upper_bound(str(upper_bound))

        if not error:
            self.fit_curve()

    def set_results(self, error="") -> None:
        """Set the results dialog based on the fit"""
        initial_string = _("Results:") + "\n"
        buffer_string = initial_string
        if error == "value":
            buffer_string += \
                _("Please enter valid fitting \nparameters to start the fit")
        elif error == "equation":
            buffer_string += \
                _("Please enter a valid equation \nto start the fit")
        elif error == "bounds":
            buffer_string += \
                _("Please enter valid fitting bounds \nto start the fit")
        else:
            for index, arg in enumerate(self.get_free_variables()):
                parameter = utilities.sig_fig_round(self.param[index], 3)
                sigma = utilities.sig_fig_round(self.sigma[index], 3)
                buffer_string += f"{arg}: {parameter}"
                if self.settings.get_enum("confidence") != 0:
                    buffer_string += f" (± {sigma})"
                buffer_string += "\n"
            buffer_string += "\n" + _("Sum of R²: {R2}").format(R2=self.r2)
        self.get_text_view().get_buffer().set_text(buffer_string)
        bold_tag = Gtk.TextTag(weight=700)
        self.get_text_view().get_buffer().get_tag_table().add(bold_tag)

        start_iter = self.get_text_view().get_buffer().get_start_iter()
        end_iter = self.get_text_view().get_buffer().get_start_iter()

        # Highlight first word
        while not end_iter.ends_word() and not end_iter.ends_sentence():
            end_iter.forward_char()
        self.get_text_view().get_buffer().apply_tag(
            bold_tag, start_iter, end_iter)

    @property
    def equation_string(self):
        return utilities.preprocess(str(self.get_custom_equation().get_text()))

    def fit_curve(self, *_args) -> bool:
        """
        Fit the data to the equation in the entry, returns a boolean indicating
        whether the fit was succesfull or not.
        """
        def _get_equation_name(equation_name, values):
            var_to_val = dict(zip(self.get_free_variables(), values))

            for var, val in var_to_val.items():
                equation_name = equation_name.replace(var, str(round(val, 3)))
            return equation_name

        function = utilities.string_to_function(self.equation_string)
        if function is None:
            return
        try:
            self.param, self.param_cov = curve_fit(
                function,
                self.data_curve.xdata, self.data_curve.ydata,
                p0=self.fitting_parameters.get_p0(),
                bounds=self.fitting_parameters.get_bounds(), nan_policy="omit",
                method=self.settings.get_string("optimization"),
            )
            self.get_custom_equation().get_child().remove_css_class("error")
        except (ValueError, TypeError, _minpack.error, RuntimeError):
            # Cancel fit if not successful
            self.get_custom_equation().get_child().add_css_class("error")
            self.set_results(error="equation")
            return
        xdata = numpy.linspace(
            min(self.data_curve.xdata), max(self.data_curve.xdata), 5000,
        )
        ydata = [function(x, *self.param) for x in xdata]

        name = _get_equation_name(
            str(self.get_custom_equation().get_text()).lower(), self.param)
        self.fitted_curve.set_name(f"Y = {name}")
        self.fitted_curve.ydata, self.fitted_curve.xdata = (ydata, xdata)
        self.get_confidence(function)
        self.set_results()
        return True

    def get_confidence(self, function: str) -> None:
        """
        Get the confidence intervall in terms of the standard deviation
        resulting from the covariance in the plot. The bounds are navively
        calculated by using the extremes on each parameter for both sides
        of the bounds.
        """
        # Get standard deviation
        self.canvas.axes[0].relim()  # Reset limits
        self.sigma = numpy.sqrt(numpy.diagonal(self.param_cov))
        self.sigma *= self.settings.get_enum("confidence")
        try:
            fitted_y = \
                [function(x, *self.param) for x in self.data_curve.xdata]
        except (OverflowError, ZeroDivisionError):
            return
        ss_res = numpy.sum((numpy.asarray(self.data_curve.ydata)
                            - numpy.asarray(fitted_y)) ** 2)
        ss_sum = numpy.sum((self.data_curve.ydata - numpy.mean(fitted_y)) ** 2)
        self.r2 = utilities.sig_fig_round(1 - (ss_res / ss_sum), 3)

        # Get confidence band
        upper_bound = \
            function(self.fitted_curve.xdata, *(self.param + self.sigma))
        lower_bound = \
            function(self.fitted_curve.xdata, *(self.param - self.sigma))

        # Filter non-finite values from the bounds
        lower_bound = lower_bound[numpy.isfinite(lower_bound)]
        upper_bound = upper_bound[numpy.isfinite(upper_bound)]

        # Cancel if there's no valid values left after filtering non-finite
        if len(upper_bound) == 0 or len(lower_bound) == 0:
            return

        span = max(self.fitted_curve.ydata) - min(self.fitted_curve.ydata)
        middle = \
            (max(self.fitted_curve.ydata) - min(self.fitted_curve.ydata)) / 2

        # Don't try to draw complicated and resource-hogging bounds when
        # far out of range, instead set them to be single-values far away
        if max(upper_bound) > middle + 1e5 * span:
            upper_bound = [middle + 1e5 * span]
        if min(lower_bound) < middle - 1e5 * span:
            lower_bound = [middle - 1e5 * span]

        self.fill.props.data = (
            self.fitted_curve.props.xdata, lower_bound, upper_bound,
        )

    def add_fit(self, _widget):
        """Add fitted data to the items in the main application"""
        application = self.get_application()
        style_manager = application.get_figure_style_manager()
        application.get_data().add_items([DataItem.new(
            style_manager.get_selected_style_params(),
            name=self.fitted_curve.get_name(),
            xdata=list(self.fitted_curve.xdata),
            ydata=list(self.fitted_curve.ydata),
        )])
        self.destroy()

    def set_entry_rows(self):
        """
        Remove the old entry rows and replace them with new ones corresponding
        to the free variables in the equation
        """
        while self.get_fitting_params().get_last_child() is not None:
            self.get_fitting_params().remove(
                self.get_fitting_params().get_last_child())

        for arg in self.get_free_variables():
            self.get_fitting_params().append(FittingParameterEntry(self, arg))


class FittingParameterContainer(Data):
    """Class to contain the fitting parameters."""
    __gtype_name__ = "GraphsFittingParameterContainer"
    __gsignals__ = {}

    def add_items(self, items):
        for item in items:
            self._items[item.get_name()] = item

    def remove_unused(self, used_list):
        # First create list with items to remove
        # to avoid dict changing size during iteration
        remove_list = []
        for item in self._items.values():
            if item.get_name() not in used_list:
                remove_list.append(item.get_name())

        for item_name in remove_list:
            del self._items[item_name]

        self.order_by_list(used_list)

    def order_by_list(self, ordered_list):
        self._items = {key: self._items[key] for key in ordered_list}

    def get_p0(self) -> list:
        """Get the initial values."""
        return [float(item_.get_initial()) for item_ in self]

    def get_bounds(self):
        lower_bounds = [float(item_.get_lower_bound()) for item_ in self]
        upper_bounds = [float(item_.get_upper_bound()) for item_ in self]
        return (lower_bounds, upper_bounds)


class FittingParameter(Graphs.FittingParameter):
    """Class for the fitting parameters."""
    __gtype_name__ = "GraphsFittingParameterItem"
    application = GObject.Property(type=object)

    def __init__(self, **kwargs):
        super().__init__(name=kwargs.get("name", ""),
                         initial=kwargs.get("initial", 1),
                         lower_bound=kwargs.get("lower_bound", "-inf"),
                         upper_bound=kwargs.get("upper_bound", "inf"),
                         )


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/fitting_parameters.ui")
class FittingParameterEntry(Gtk.Box):
    __gtype_name__ = "GraphsFittingParameterEntry"
    label = Gtk.Template.Child()
    initial = Gtk.Template.Child()
    upper_bound = Gtk.Template.Child()
    lower_bound = Gtk.Template.Child()
    lower_bound_group = Gtk.Template.Child()
    upper_bound_group = Gtk.Template.Child()

    application = GObject.Property(type=Adw.Application)

    def __init__(self, parent, arg):
        super().__init__(application=parent.get_application())
        self.parent = parent
        self.params = parent.fitting_parameters[arg]
        fitting_param_string = _("Fitting Parameters for {param_name}").format(
            param_name=self.params.get_name())
        self.label.set_markup(
            f"<b> {fitting_param_string}: </b>")
        self.initial.set_text(str(self.params.get_initial()))
        self.initial.connect("notify::text", parent.on_entry_change)
        self.upper_bound.connect("notify::text", parent.on_entry_change)
        self.lower_bound.connect("notify::text", parent.on_entry_change)
        self.set_bounds_visibility()

    def set_bounds_visibility(self):
        method = self.parent.settings.get_string("optimization")
        self.upper_bound_group.set_visible(method != "lm")
        self.lower_bound_group.set_visible(method != "lm")
