# SPDX-License-Identifier: GPL-3.0-or-later
import logging

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
    confirm_button = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        config = parent.preferences.config
        self.equation.set_text(config["addequation_equation"])
        self.x_start.set_text(config["addequation_x_start"])
        self.x_stop.set_text(config["addequation_x_stop"])
        self.step_size.set_text(config["addequation_step_size"])
        self.confirm_button.connect("clicked", self.on_accept, parent)
        self.set_transient_for(parent.main_window)
        self.present()

    def on_accept(self, _widget, parent):
        """Launched when the accept button is pressed on the equation window"""
        x_start = self.x_start.get_text()
        x_stop = self.x_stop.get_text()
        step_size = self.step_size.get_text()
        equation = str(self.equation.get_text())
        try:
            xdata, ydata = calculation.create_dataset(
                x_start, x_stop, equation, step_size)
            name = str(self.name.get_text())
            if name == "":
                name = f"Y = {equation}"
            graphs.add_item(parent, Item(parent, xdata, ydata, name))
            self.destroy()
        except (NameError, SyntaxError) as exception:
            exception_type = exception.__class__.__name__
            toast = f"{exception_type} - Unable to add data from equation"
            self.toast_overlay.add_toast(Adw.Toast(title=toast))
            logging.exception(toast)
