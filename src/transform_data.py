from gi.repository import Gtk, Adw, GObject, Gio
from numpy import *
from . import item_operations, plotting_tools

def open_transform_window(widget, _, self):
    win = TransformWindow(self)
    name = "transform_confirm"
    button = win.transform_confirm_button
    button.set_sensitive(True)
    button.connect("clicked", on_accept, self, win)
    win.present()
    pass

def on_accept(widget, self, window):
    input_x = str(window.transform_x_entry.get_text())
    input_y = str(window.transform_y_entry.get_text())
    operation(self, input_x, input_y)
    window.destroy()

def operation(self, input_x, input_y):
    x_data = self.datadict
    selected_keys = item_operations.get_selected_keys(self)
    for key in selected_keys:
        x_array = []
        y_array = []
        Y_range = self.datadict[key].ydata
        X_range = self.datadict[key].xdata
        operations = []
        for xy_operation in [input_x, input_y]:
            xy_operation = xy_operation.replace("Y_range", "y_range")
            xy_operation = xy_operation.replace("X_range", "x_range")
            xy_operation = xy_operation.replace("Y", "self.datadict[key].ydata[index]")
            xy_operation = xy_operation.replace("X", "self.datadict[key].xdata[index]")
            xy_operation = xy_operation.replace("y_range", "Y_range")
            xy_operation = xy_operation.replace("x_range", "X_range")
            xy_operation = xy_operation.replace("^", "**")
            operations.append(xy_operation)

        x_operation, y_operation = operations[0], operations[1]
        for index, value in enumerate(self.datadict[key].xdata):
            x_array.append(eval(x_operation))
            y_array.append(eval(y_operation))
        self.datadict[key].xdata = x_array
        self.datadict[key].ydata = y_array

    item_operations.add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

@Gtk.Template(resource_path="/se/sjoerd/DatMan/transform_window.ui")
class TransformWindow(Adw.Window):
    __gtype_name__ = "TransformWindow"
    transform_x_entry = Gtk.Template.Child()
    transform_y_entry = Gtk.Template.Child()
    transform_confirm_button = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        style_context = self.transform_confirm_button.get_style_context()
        style_context.add_class("suggested-action")

