# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, Gtk

from graphs import ui, utilities
from graphs.item import DataItem

import numexpr

import numpy


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/add_equation_window.ui")
class AddEquationWindow(Adw.Window):
    __gtype_name__ = "GraphsAddEquationWindow"

    equation = Gtk.Template.Child()
    x_start = Gtk.Template.Child()
    x_stop = Gtk.Template.Child()
    step_size = Gtk.Template.Child()
    name = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(application=application,
                         transient_for=application.get_window())
        ui.bind_values_to_settings(
            self.get_application().get_settings("add-equation"), self)
        self.present()

    @Gtk.Template.Callback()
    def on_accept(self, _widget):
        """Launched when the accept button is pressed on the equation window"""
        values = ui.save_values_to_dict(
            self, ["equation", "step-size", "x-start", "x-stop"],
        )
        try:
            x_start = utilities.string_to_float(values["x-start"])
            x_stop = utilities.string_to_float(values["x-stop"])
            step_size = utilities.string_to_float(values["step-size"])
            datapoints = int(abs(x_start - x_stop) / step_size) + 1
            xdata = numpy.ndarray.tolist(
                numpy.linspace(x_start, x_stop, datapoints),
            )
            equation = utilities.preprocess(values["equation"])
            ydata = numpy.ndarray.tolist(
                numexpr.evaluate(equation + " + x*0", local_dict={"x": xdata}),
            )
            name = str(self.name.get_text())
            if name == "":
                name = f"Y = {values['equation']}"
            application = self.get_application()
            style_manager = application.get_figure_style_manager()
            application.get_data().add_items([DataItem.new(
                style_manager.get_selected_style_params(),
                xdata, ydata, name=name,
            )])
            self.destroy()
        except ValueError as error:
            self.toast_overlay.add_toast(Adw.Toast(title=error))
        except (NameError, SyntaxError, TypeError) as exception:
            toast = _("{error} - Unable to add data from equation").format(
                error=exception.__class__.__name__)
            self.toast_overlay.add_toast(Adw.Toast(title=toast))
            logging.exception(toast)
