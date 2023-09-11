# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import copy
import numpy

from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, GLib, GObject, Gio, Gtk
from scipy.optimize import curve_fit

from graphs import ui, utilities
from graphs.canvas import Canvas
from graphs.data import Data
from graphs.item import Item

@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/curve_fitting.ui")
class CurveFittingWindow(Adw.Window):
    __gtype_name__ = "CurveFittingWindow"
    dpi = Gtk.Template.Child()
    file_format = Gtk.Template.Child()
    transparent = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    file_formats = GObject.Property(type=object)

    def __init__(self, application, item):
        self._canvas = application.get_window().get_canvas()
        super().__init__(
            application=application, transient_for=application.get_window(),
            file_formats=self._canvas.get_supported_filetypes_grouped(),
        )
        self.file_format.set_model(
            Gtk.StringList.new(list(self.file_formats.keys())))
        ui.bind_values_to_settings(
            self.get_application().get_settings("export-figure"), self)
        canvas = Canvas(application)

        self.item = item

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

    @Gtk.Template.Callback()
    def fit_curve(self, _widget):
        def test(x, a, b):
            return a * x + b
        param, param_cov = curve_fit(test, self.item.xdata, self.item.ydata)
        self.curves[0].name = f"{param[0]}*x + {param[1]}"
        self.curves[0].ydata, self.curves[0].xdata = (
            numpy.asarray(self.item.xdata) * param[0] + param[1],
            self.curves[1].xdata)

    def set_canvas(self, canvas):
        self.toast_overlay.set_child(canvas)

    def get_canvas(self):
        widget = self.toast_overlay.get_child()
        return None if isinstance(widget, Adw.StatusPage) else widget        
