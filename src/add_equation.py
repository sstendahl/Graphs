# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, Gtk

from graphs import calculation, ui, utilities
from graphs.item import Item

KEYS = ["equation", "step-size", "x-start", "x-stop"]


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/add_equation_window.ui")
class AddEquationWindow(Adw.Window):
    __gtype_name__ = "AddEquationWindow"
    equation = Gtk.Template.Child()
    x_start = Gtk.Template.Child()
    x_stop = Gtk.Template.Child()
    step_size = Gtk.Template.Child()
    name = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(application=application,
                         transient_for=application.main_window)
        ui.bind_values_to_settings(
            self.props.application.get_settings("add-equation"), self)
        self.present()

    @Gtk.Template.Callback()
    def on_accept(self, _widget):
        """Launched when the accept button is pressed on the equation window"""
        values = ui.save_values_to_dict(self, KEYS)
        try:
            xdata, ydata = calculation.create_dataset(
                utilities.string_to_float(values["x-start"]),
                utilities.string_to_float(values["x-stop"]),
                values["equation"],
                utilities.string_to_float(values["step-size"]),
            )
            name = str(self.name.get_text())
            if name == "":
                name = f"Y = {values['equation']}"
            self.props.application.props.data.add_items(
                [Item.new(self.props.application, xdata, ydata, name=name)],
            )
            self.destroy()
        except ValueError as error:
            self.toast_overlay.add_toast(Adw.Toast(title=error))
        except (NameError, SyntaxError, TypeError) as exception:
            toast = _("{error} - Unable to add data from equation").format(
                error=exception.__class__.__name__)
            self.toast_overlay.add_toast(Adw.Toast(title=toast))
            logging.exception(toast)
