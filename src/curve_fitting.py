# SPDX-License-Identifier: GPL-3.0-or-later
import re

from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, GLib, GObject, Gio, Gtk
from scipy.optimize import curve_fit
from sympy import symbols, lambdify, sympify

from graphs import ui, utilities
from graphs.canvas import Canvas
from graphs.data import Data
from graphs.item import Item

@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/curve_fitting.ui")
class CurveFittingWindow(Adw.Window):
    __gtype_name__ = "CurveFittingWindow"
    dpi = Gtk.Template.Child()
    equation_entry = Gtk.Template.Child()
    transparent = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, application, item):
        self._canvas = application.get_window().get_canvas()
        super().__init__(
            application=application, transient_for=application.get_window(),

        )
        ui.bind_values_to_settings(
            self.get_application().get_settings("export-figure"), self)
        canvas = Canvas(application)

        self.item = item
        self._equation = str(self.equation_entry.get_text())

        self.curves = Data(application)

        data_curve = Item.new(
        application, xdata=item.xdata, ydata=item.ydata, name=item.name)
        data_curve.linestyle = 0
        data_curve.markerstyle = 1
        data_curve.markersize = 13
        fitted_curve = Item.new(
        application, xdata=[], ydata=[], color="#A51D2D")

        self.curves.add_items([fitted_curve, data_curve])

        for item_ in self.curves:
            item_.disconnect(0)


        figure_settings = application.get_figure_settings()
        for prop in dir(figure_settings.props):
            if prop not in ["use_custom_style", "custom_style"]:
                figure_settings.bind_property(prop, canvas, prop, 1 | 2)

        self.curves.bind_property("items", canvas, "items", 2)
        self.set_canvas(canvas)
        self.present()

    @property
    def equation(self):
	    return str(self.equation_entry.get_text())


    @Gtk.Template.Callback()
    def fit_curve(self, _widget):

        def create_function(equation_name):
            # Extract variables from the string
            variables = \
                re.findall(r'\b(?!x\b|X\b|sin\b|cos\b|tan\b)[a-wy-zA-WY-Z]+\b',
                equation_name)
            variables = ['x'] + variables

            sym_vars = symbols(variables)
            symbolic = sympify(equation_name,
                locals=dict(zip(variables, sym_vars)))
            function = lambdify(sym_vars, symbolic)
            return function

        def get_equation_name(equation_name, values):
            variables = \
                re.findall(r'\b(?!x\b|X\b|sin\b|cos\b|tan\b)[a-wy-zA-WY-Z]+\b',
                equation_name)
            var_to_val = dict(zip(variables, values))

            for var, val in var_to_val.items():
                equation_name = equation_name.replace(var, str(val))
            return equation_name


        function = create_function(self.equation)
        param, param_cov = curve_fit(function, self.item.xdata, self.item.ydata)
        ydata_fit = [function(x, *param) for x in self.item.xdata]
        name = get_equation_name(self.equation, param)

        self.curves[0].name = name
        self.curves[0].ydata, self.curves[0].xdata = (
            ydata_fit, self.curves[1].xdata)


    def set_canvas(self, canvas):
        self.toast_overlay.set_child(canvas)

    def get_canvas(self):
        widget = self.toast_overlay.get_child()
        return None if isinstance(widget, Adw.StatusPage) else widget        
