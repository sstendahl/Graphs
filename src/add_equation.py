# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, Gtk

from graphs import calculation, graphs
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
        super().__init__(application=application)
        self.set_transient_for(self.props.application.main_window)
        config = self.props.application.preferences.config
        self.equation.set_text(config["addequation_equation"])
        self.x_start.set_text(config["addequation_x_start"])
        self.x_stop.set_text(config["addequation_x_stop"])
        self.step_size.set_text(config["addequation_step_size"])
        self.present()

    @Gtk.Template.Callback()
    def on_accept(self, _widget):
        """Launched when the accept button is pressed on the equation window"""
        try:
            equation = str(self.equation.get_text())
            xdata, ydata = calculation.create_dataset(
                self.x_start.get_text(),
                self.x_stop.get_text(),
                equation,
                self.step_size.get_text())
            name = str(self.name.get_text())
            if name == "":
                name = f"Y = {equation}"
            graphs.add_items(
                self.props.application,
                [Item(self.props.application, xdata, ydata, name)])
            self.destroy()
        except (NameError, SyntaxError) as exception:
            toast = _("{error} - Unable to add data from equation").format(
                error=exception.__class__.__name__)
            self.toast_overlay.add_toast(Adw.Toast(title=toast))
            logging.exception(toast)
