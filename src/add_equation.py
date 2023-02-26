# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

from graphs import graphs, plotting_tools, utilities
from graphs.data import Data

import numpy
from numpy import *


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
        self.x_start_entry.set_text(cfg["addequation_X_start"])
        self.x_stop_entry.set_text(cfg["addequation_X_stop"])
        self.equation_entry.set_text(cfg["addequation_equation"])
        self.confirm_button.connect("clicked", self.on_accept, parent)
        self.set_transient_for(parent.main_window)

    def on_accept(self, _widget, parent):
        """Launched when the accept button is pressed on the equation window"""
        x_start = self.x_start_entry.get_text()
        x_stop = self.x_stop_entry.get_text()
        step_size = self.step_size_entry.get_text()
        equation = str(self.equation_entry.get_text())
        dataset = utilities.create_dataset(
            x_start, x_stop, equation, step_size,
            str(self.name_entry.get_text()))
        try:
            new_file = Data(parent, dataset["xdata"], dataset["ydata"])
            new_file.filename = dataset["name"]
        except Exception as exception:
            exception_type = exception.__class__.__name__
            toast = f"{exception_type} - Unable to add data from equation"
            self.toast_overlay.add_toast(Adw.Toast(title=toast))
            return

        # Choose how to handle duplicates filenames. Add them,
        # ignore them, overide them, Or rename the file
        handle_duplicates = parent.preferences.config["handle_duplicates"]
        if not handle_duplicates == "Add duplicates":
            for key, item in parent.datadict.items():
                if new_file.filename in item.filename:
                    if handle_duplicates == "Auto-rename duplicates":
                        new_file.filename = utilities.get_duplicate_filename(
                            parent, new_file.filename)
                    elif handle_duplicates == "Ignore duplicates":
                        toast = "Item with this name already exists"
                        self.toast_overlay.add_toast(Adw.Toast(title=toast))
                        return
                    elif handle_duplicates == "Override existing items":
                        new_file.xdata_clipboard = [new_file.xdata.copy()]
                        new_file.ydata_clipboard = [new_file.ydata.copy()]
                        new_file.clipboard_pos = -1
                        parent.datadict[key] = new_file
                        plotting_tools.refresh_plot(parent)
                        self.destroy()
                        return

        new_file.xdata_clipboard = [new_file.xdata.copy()]
        new_file.ydata_clipboard = [new_file.ydata.copy()]
        new_file.clipboard_pos = -1
        color = plotting_tools.get_next_color(parent)
        parent.datadict[new_file.key] = new_file
        graphs.add_sample_to_menu(
            parent, new_file.filename, color, new_file.key, True)
        plotting_tools.refresh_plot(parent)
        self.destroy()
