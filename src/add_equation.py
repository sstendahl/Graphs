# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, Gtk

from graphs import calculation, graphs, utilities
from graphs.item import Item


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/add_equation_window.ui")
class AddEquationWindow(Adw.Window):
    __gtype_name__ = "AddEquationWindow"
    toast_overlay = Gtk.Template.Child()
    equation = Gtk.Template.Child()
    name = Gtk.Template.Child()
    x_start = Gtk.Template.Child()
    x_stop = Gtk.Template.Child()
    step_size = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(application=application,
                         transient_for=application.main_window)
        preferences = self.props.application.preferences
        self.equation.set_text(preferences["addequation_equation"])
        self.x_start.set_text(preferences["addequation_x_start"])
        self.x_stop.set_text(preferences["addequation_x_stop"])
        self.step_size.set_text(preferences["addequation_step_size"])
        self.present()

    @Gtk.Template.Callback()
    def on_accept(self, _widget):
        """Launched when the accept button is pressed on the equation window"""
        try:
            equation = str(self.equation.get_text())
            xdata, ydata = calculation.create_dataset(
                utilities.string_to_float(self.x_start.get_text()),
                utilities.string_to_float(self.x_stop.get_text()),
                equation,
                utilities.string_to_float(self.step_size.get_text()),
            )
            name = str(self.name.get_text())
            if name == "":
                name = f"Y = {equation}"
            graphs.add_items(
                self.props.application,
                [Item(self.props.application, xdata, ydata, name)])
            self.destroy()
        except ValueError as error:
            self.toast_overlay.add_toast(Adw.Toast(title=error))
        except (NameError, SyntaxError, TypeError) as exception:
            toast = _("{error} - Unable to add data from equation").format(
                error=exception.__class__.__name__)
            self.toast_overlay.add_toast(Adw.Toast(title=toast))
            logging.exception(toast)
