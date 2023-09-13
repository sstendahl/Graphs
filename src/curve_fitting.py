# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import re
from gettext import gettext as _

from gi.repository import Adw, Gtk

from graphs.canvas import Canvas
from graphs.data import Data
from graphs.item import Item
from graphs.utilities import preprocess, string_to_function

from scipy.optimize import curve_fit

import numpy


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/curve_fitting.ui")
class CurveFittingWindow(Adw.Window):
    __gtype_name__ = "CurveFittingWindow"
    equation_entry = Gtk.Template.Child()
    fitting_params = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    text_view = Gtk.Template.Child()

    def __init__(self, application, item):
        super().__init__(
            application=application, transient_for=application.get_window(),

        )
        canvas = Canvas(application)
        self.item = item
        self.param = []
        self.curves = Data(application)
        self.equation_entry.connect("notify::text", self.on_equation_change)
        self.entries = []
        for _var in self.get_free_variables():
            self.entries.append(1)

        data_curve = Item.new(
            application, xdata=item.xdata, ydata=item.ydata, name=item.name)
        data_curve.linestyle = 0
        data_curve.markerstyle = 1
        data_curve.markersize = 13
        fitted_curve = Item.new(
            application, xdata=[], ydata=[], color="#A51D2D")

        self.curves.add_items([fitted_curve, data_curve])
        self.fit_curve()
        self.set_entry_rows()

        for item_ in self.curves:
            item_.disconnect(0)

        figure_settings = application.get_figure_settings()
        for prop in dir(figure_settings.props):
            if prop not in ["use_custom_style", "custom_style"]:
                figure_settings.bind_property(prop, canvas, prop, 1 | 2)

        self.curves.bind_property("items", canvas, "items", 2)
        self.set_canvas(canvas)
        self.present()

    def get_free_variables(self):
        return (
            re.findall(
                r"\b(?!x\b|X\b|sin\b|cos\b|tan\b)[a-wy-zA-WY-Z]+\b",
                self.equation))

    def on_equation_change(self, _entry, _param):
        self.entries = []

        for _var in self.get_free_variables():
            self.entries.append(1)
        fit = self.fit_curve()
        if fit:
            self.set_entry_rows()

    def on_entry_change(self, entry, _param):
        for index, row in enumerate(self.fitting_params):
            if row == entry:
                self.entries[index] = entry.get_text()

        self.fit_curve()

    def set_results(self):
        initial_string = _("Results: \n")
        buffer_string = initial_string
        for index, arg in enumerate(self.get_free_variables()):
            buffer_string += f"\n {arg}: {self.param[index]}"

        self.entries = copy.deepcopy(self.param)

        self.text_view.get_buffer().set_text(buffer_string)
        bold_tag = Gtk.TextTag(weight=700)
        self.text_view.get_buffer().get_tag_table().add(bold_tag)

        start_iter = self.text_view.get_buffer().get_start_iter()
        end_iter = self.text_view.get_buffer().get_start_iter()

        while not end_iter.ends_word() and not end_iter.ends_sentence():
            end_iter.forward_char()
        self.text_view.get_buffer().apply_tag(bold_tag, start_iter, end_iter)

    @property
    def equation(self):
        return preprocess(str(self.equation_entry.get_text()))

    def fit_curve(self):
        def _get_equation_name(equation_name, values):
            var_to_val = dict(zip(self.get_free_variables(), values))

            for var, val in var_to_val.items():
                equation_name = equation_name.replace(var, str(round(val, 3)))
            return equation_name

        function = string_to_function(self.equation)
        if function is None:
            return

        param, param_cov = curve_fit(function, self.item.xdata,
                                     self.item.ydata, p0=self.entries)

        xdata = numpy.linspace(
            min(self.curves[1].xdata),
            max(self.curves[1].xdata),
            5000)

        ydata_fit = [function(x, *param) for x in xdata]
        name = _get_equation_name(str(self.equation_entry.get_text()), param)

        self.param = param
        self.curves[0].name = f"Y = {name}"
        self.curves[0].ydata, self.curves[0].xdata = (
            ydata_fit, xdata)

        self.set_results()
        return True

    @Gtk.Template.Callback()
    def add_fit(self, _widget):
        self.get_application().get_data().add_items([self.curves[0]])
        self.destroy()

    def set_entry_rows(self):

        while self.fitting_params.get_last_child() is not None:
            self.fitting_params.remove(self.fitting_params.get_last_child())

        for index, arg in enumerate(self.get_free_variables()):
            entryrow = Adw.EntryRow.new()
            entryrow.set_title(_(f"Initial guess {arg}:"))
            entryrow.set_css_classes(["card"])
            entryrow.set_text(f"{self.entries[index]}")
            entryrow.connect("notify::text", self.on_entry_change)
            self.fitting_params.append(entryrow)

    def set_canvas(self, canvas):
        self.toast_overlay.set_child(canvas)

    def get_canvas(self):
        widget = self.toast_overlay.get_child()
        return None if isinstance(widget, Adw.StatusPage) else widget
