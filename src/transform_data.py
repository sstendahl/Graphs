# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from gi.repository import Adw, Gtk

from graphs import calculation, operation_tools
from graphs import clipboard, plotting_tools, utilities
from graphs.misc import InteractionMode


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/transform_window.ui")
class TransformWindow(Adw.Window):
    __gtype_name__ = "TransformWindow"
    transform_x_entry = Gtk.Template.Child()
    transform_y_entry = Gtk.Template.Child()
    confirm_button = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.transform_x_entry.set_text("X")
        self.transform_y_entry.set_text("Y")
        self.confirm_button.connect("clicked", self.accept, parent)
        self.set_transient_for(parent.main_window)
        self.present()

    def accept(self, _widget, parent):
        input_x = str(self.transform_x_entry.get_text())
        input_y = str(self.transform_y_entry.get_text())
        selected_keys = utilities.get_selected_keys(parent)
        if parent.interaction_mode == InteractionMode.SELECT:
            _selection, start_stop = operation_tools.select_data(parent)

        for key in selected_keys:
            if f"{key}_selected" in parent.datadict:
                start_index = start_stop[key][0]
                stop_index = start_stop[key][1]
                xdata_in = parent.datadict[key].xdata[start_index:stop_index]
                try:
                    xdata_out, ydata_out = calculation.operation(
                        xdata_in, input_x, input_y)
                except Exception as exception:
                    exception_type = exception.__class__.__name__
                    toast = f"{exception_type}: Unable to do transformation, "
                    + "make sure the syntax is correct"
                    parent.main_window.add_toast(toast)
                    logging.exception("Unable to do transformation")
                    return
                parent.datadict[key].xdata[start_index:stop_index] = xdata_out
                parent.datadict[key].ydata[start_index:stop_index] = ydata_out
            if parent.interaction_mode != InteractionMode.SELECT:
                xdata_in = parent.datadict[key].xdata
                ydata_in = parent.datadict[key].ydata
                try:
                    xdata_out, ydata_out = calculation.operation(
                        xdata_in, ydata_in, input_x, input_y)
                except Exception as exception:
                    exception_type = exception.__class__.__name__
                    toast = f"{exception_type}: Unable to do transformation, \
make sure the syntax is correct"
                    parent.main_window.add_toast(toast)
                    logging.exception("Unable to do transformation")
                    return
                parent.datadict[key].xdata = xdata_out
                parent.datadict[key].ydata = ydata_out
            parent.datadict[key].xdata, parent.datadict[
                key].ydata = operation_tools.sort_data(
                    parent.datadict[key].xdata, parent.datadict[key].ydata)
        for key in parent.datadict.copy():
            if key.endswith("_selected"):
                del (parent.datadict[key])
        clipboard.add(parent)
        plotting_tools.refresh_plot(parent)
        self.destroy()
