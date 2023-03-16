# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from gi.repository import Adw, Gtk

from graphs import calculation, graphs, plotting_tools
from graphs.data import Data


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/add_equation_window.ui")
class AddEquationWindow(Adw.Window):
    __gtype_name__ = "AddEquationWindow"
    confirm_button = Gtk.Template.Child()
    step_size_entry = Gtk.Template.Child()
    x_stop_entry = Gtk.Template.Child()
    x_start_entry = Gtk.Template.Child()
    equation_entry = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        cfg = parent.preferences.config
        self.step_size_entry.set_text(cfg["addequation_step_size"])
        self.x_start_entry.set_text(cfg["addequation_x_start"])
        self.x_stop_entry.set_text(cfg["addequation_x_stop"])
        self.equation_entry.set_text(cfg["addequation_equation"])
        self.confirm_button.connect("clicked", self.on_accept, parent)
        self.set_transient_for(parent.main_window)
        self.present()

    def on_accept(self, _widget, parent):
        """Launched when the accept button is pressed on the equation window"""
        x_start = self.x_start_entry.get_text()
        x_stop = self.x_stop_entry.get_text()
        step_size = self.step_size_entry.get_text()
        equation = str(self.equation_entry.get_text())
        xdata, ydata = calculation.create_dataset(
            x_start, x_stop, equation, step_size)
        name = str(self.name_entry.get_text())
        if name == "":
            name = f"Y = {str(equation)}"
        try:
            new_file = Data(parent, xdata, ydata)
            new_file.filename = name
            new_file.color = plotting_tools.get_next_color(parent)
            graphs.add_item(parent, new_file)
            self.destroy()
        except Exception as exception:
            exception_type = exception.__class__.__name__
            toast = f"{exception_type} - Unable to add data from equation"
            self.toast_overlay.add_toast(Adw.Toast(title=toast))
            logging.exception(toast)
