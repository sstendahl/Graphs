# SPDX-License-Identifier: GPL-3.0-or-later
import re
from gettext import gettext as _

from gi.repository import Adw, GObject, Graphs, Gtk

from graphs import ui, utilities
from graphs.canvas import Canvas
from graphs.data import Data
from graphs.item import DataItem

import matplotlib
import numpy

from scipy.optimize import curve_fit


class CurveFittingWindow(Graphs.CurveFittingTool):
    __gtype_name__ = "GraphsCurveFittingWindow"
    confirm_button = GObject.Property(type=Gtk.Button)
    equation = GObject.Property(type=Adw.EntryRow)
    fitting_params = GObject.Property(type=Gtk.Box)
    text_view = GObject.Property(type=Gtk.TextView)
    toast_overlay = GObject.Property(type=Adw.ToastOverlay)

    def __init__(self, application, item):
        figure_settings = \
            Graphs.FigureSettings.new(
                application.get_settings().get_child("figure"))
        super().__init__(
            application=application, transient_for=application.get_window(),
            figure_settings=figure_settings,
        )
        self.equation = self.get_equation()
        ui.bind_values_to_settings(
            self.get_application().get_settings("curve-fitting"), self)
        self.get_confirm_button().connect("clicked", self.add_fit)
        canvas = Canvas(application)
        self.param = []
        self.sigma = []
        self.r2 = 0

        for prop in dir(figure_settings.props):
            if prop not in ["use_custom_style", "custom_style"]:
                figure_settings.bind_property(prop, canvas, prop, 1 | 2)
        self.get_equation().connect("notify::text", self.on_equation_change)
        self.fitting_parameters = FittingParameterContainer(application)

        for var in self.get_free_variables():
            self.fitting_parameters.add_items([FittingParameter(name=var)])
        # Generate item for the data that is fitted to
        self.data_curve = DataItem.new(
            application, xdata=item.xdata,
            ydata=item.ydata, name=item.get_name(),
            color="#1A5FB4",
        )
        self.data_curve.linestyle = 0
        self.data_curve.markerstyle = 1
        self.data_curve.markersize = 13

        # Generate item for the fit
        self.fitted_curve = DataItem.new(
            application, xdata=[], ydata=[], color="#A51D2D", name=" ",
        )

        canvas.props.items = [self.fitted_curve, self.data_curve]

        # Scale axis to the data to be fitted, set linear scale

        self.canvas = canvas
        self.fit_curve()
        self.set_entry_rows()
        self.get_toast_overlay().set_child(canvas)
        self.set_canvas()
        self.present()

    def set_canvas(self):
        self.canvas.axis.yscale = "linear"
        self.canvas.axis.xscale = "linear"
        self.canvas.highlight_enabled = False
        figure_settings = self.get_figure_settings()

        xdata = list(self.data_curve.xdata)
        ydata = list(self.data_curve.ydata)
        xdata_fit = list(self.fitted_curve.xdata)
        ydata_fit = list(self.fitted_curve.ydata)
        upper_bound = list(self.upper_bound)
        lower_bound = list(self.lower_bound)

        ymax = max(ydata + ydata_fit + upper_bound)
        ymin = min(ydata + ydata_fit + lower_bound)
        xmax = max(xdata + xdata_fit)
        xmin = min(xdata + xdata_fit)

        xmin -= 0.015 * (xmax - xmin)
        xmax += 0.015 * (xmax - xmin)
        ymin -= 0.05 * (ymax - ymin)
        ymax += 0.05 * (ymax - ymin)

        figure_settings.set_property("min_left", ymin)
        figure_settings.set_property("max_left", ymax)
        figure_settings.set_property("min_bottom", xmin)
        figure_settings.set_property("max_bottom", xmax)

    def get_free_variables(self):
        return re.findall(
            r"\b(?!x\b|X\b|sin\b|cos\b|tan\b)[a-wy-zA-WY-Z]+\b",
            self.equation_string,
        )

    def on_equation_change(self, _entry, _param):
        for var in self.get_free_variables():
            if var not in self.fitting_parameters.get_names():
                self.fitting_parameters.add_items([FittingParameter(name=var)])
        self.fitting_parameters.remove_unused(self.get_free_variables())
        fit = self.fit_curve()
        if fit:
            self.set_entry_rows()

    def on_entry_change(self, entry, _param):
        def is_float(value):
            try:
                float(value)
                return True
            except ValueError:
                return False

        for index, row in enumerate(self.get_fitting_params()):
            param_entries = entry

            # Get the FittingParameterEntry class corresponding to the entry
            while True:
                if isinstance(param_entries, FittingParameterEntry):
                    break
                param_entries = param_entries.get_parent()

            # Set the parameters for the row corresponding to the entry that
            # was edited
            if row == param_entries:
                initial = param_entries.initial.get_text()
                lower_bound = param_entries.lower_bound.get_text()
                upper_bound = param_entries.upper_bound.get_text()

                new_initial = (float(initial) if is_float(initial) else 1)
                new_lower_bound = (
                    lower_bound if is_float(lower_bound) else "inf")
                new_upper_bound = (
                    upper_bound if is_float(upper_bound) else "-inf")
                self.fitting_parameters[index].set_initial(new_initial)
                self.fitting_parameters[index].set_lower_bound(new_lower_bound)
                self.fitting_parameters[index].set_upper_bound(new_upper_bound)
        self.fit_curve()

    def set_results(self):
        initial_string = _("Results: \n")
        buffer_string = initial_string
        for index, arg in enumerate(self.get_free_variables()):
            parameter = utilities.sig_fig_round(self.param[index], 3)
            sigma = utilities.sig_fig_round(self.sigma[index], 3)
            buffer_string += f"\n {arg}: {parameter}"
            buffer_string += f" (± {sigma})"
        buffer_string += f"\n\nSum of R²: {self.r2}"

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
        return utilities.preprocess(str(self.get_equation().get_text()))

    def fit_curve(self):
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
            )
        except (ValueError, TypeError):
            # Cancel fit if not succesfull
            return
        xdata = numpy.linspace(
            min(self.data_curve.xdata), max(self.data_curve.xdata), 5000,
        )
        ydata = [function(x, *self.param) for x in xdata]

        name = _get_equation_name(
            str(self.get_equation().get_text()), self.param)
        self.fitted_curve.set_name(f"Y = {name}")
        self.fitted_curve.ydata, self.fitted_curve.xdata = (ydata, xdata)
        self.get_confidence(function)
        self.set_results()
        self.set_canvas()
        return True

    def get_confidence(self, function):
        # Get standard deviation
        self.sigma = numpy.sqrt(numpy.diagonal(self.param_cov))
        fitted_y = [function(x, *self.param) for x in self.data_curve.xdata]
        ss_res = numpy.sum((numpy.asarray(self.data_curve.ydata)
                            - numpy.asarray(fitted_y)) ** 2)
        ss_sum = numpy.sum((self.data_curve.ydata - numpy.mean(fitted_y)) ** 2)
        self.r2 = 1 - (ss_res / ss_sum)

        # Get confidence band
        self.upper_bound = \
            list(function(self.fitted_curve.xdata, *(self.param + self.sigma)))
        self.lower_bound = \
            list(function(self.fitted_curve.xdata, *(self.param - self.sigma)))
        for collection in self.canvas.axis.collections:
            if isinstance(collection, matplotlib.collections.PolyCollection):
                collection.remove()
        self.canvas.axis.fill_between(self.fitted_curve.xdata,
                                      self.lower_bound,
                                      self.upper_bound,
                                      color=self.canvas.rubberband_fill_color,
                                      alpha=0.15)

    def add_fit(self, _widget):
        """Add fitted data to the items in the main application"""
        self.get_application().get_data().add_items([DataItem.new(
            self.get_application(), name=self.fitted_curve.get_name(),
            xdata=self.fitted_curve.xdata, ydata=self.fitted_curve.ydata,
        )])
        self.destroy()

    def set_entry_rows(self):
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

    application = GObject.Property(type=Adw.Application)

    def __init__(self, parent, arg):
        super().__init__(application=parent.get_application())
        self.parent = parent
        self.params = parent.fitting_parameters[arg]
        self.label.set_markup(
            f"<b>Fitting parameters for {self.params.get_name()}: </b>")
        self.initial.set_text(str(self.params.get_initial()))

        self.initial.connect("notify::text", parent.on_entry_change)
        self.upper_bound.connect("notify::text", parent.on_entry_change)
        self.lower_bound.connect("notify::text", parent.on_entry_change)
