from gi.repository import Gtk, Adw, GObject, Gio
import uuid
from numpy import *
from . import item_operations, plotting_tools, datman
from .data import Data

def open_add_equation_window(widget, _, self):
    win = AddEquationWindow(self)
    win.set_transient_for(self.props.active_window)
    win.set_modal(True)
    name = "transform_confirm"
    button = win.add_equation_confirm_button
    button.connect("clicked", on_accept, self, win)
    win.present()

def on_accept(widget, self, window):
    x_start = window.X_start_entry.get_text()
    x_stop = window.X_stop_entry.get_text()
    step_size = window.step_size_entry.get_text()
    equation = str(window.equation_entry.get_text())
    try:
        new_file = create_data(self, x_start, x_stop, equation, step_size, str(window.name_entry.get_text()))
        name = new_file.filename
    except Exception as e:
        exception_type = e.__class__.__name__
        window.toast_overlay.add_toast(Adw.Toast(title=f"{exception_type} - Unable to add data from equation"))
    handle_duplicates = self.preferences.config["handle_duplicates"]
    if not handle_duplicates == "Add duplicates":
        for key, item in self.datadict.items():
            if name == item.filename:
                if handle_duplicates == "Auto-rename duplicates":
                    new_file.filename = datman.get_duplicate_filename(self, name)
                elif handle_duplicates == "Ignore duplicates":
                    window.toast_overlay.add_toast(Adw.Toast(title="Item with this name already exists"))
                    return
                elif handle_duplicates == "Override existing items":
                    new_file.xdata_clipboard = [new_file.xdata]
                    new_file.ydata_clipboard = [new_file.ydata]
                    new_file.clipboard_pos = -1
                    self.datadict[key] = new_file
                    plotting_tools.refresh_plot(self)
                    window.destroy()
                    return
        new_file.xdata_clipboard = [new_file.xdata]
        new_file.ydata_clipboard = [new_file.ydata]
        new_file.clipboard_pos = -1
        color = plotting_tools.get_next_color(self)
        self.datadict[new_file.id] = new_file
        datman.add_sample_to_menu(self, new_file.filename, color, new_file.id)
        datman.select_item(self, new_file.id)
        plotting_tools.refresh_plot(self)
        window.destroy()


def create_data(self, x_start, x_stop, equation, step_size, name):
    new_file = Data()
    new_file.id = str(uuid.uuid4())
    if name == "":
        name = f"Y = {str(equation)}"
    datapoints = int(abs(eval(x_start) - eval(x_stop))/eval(step_size))
    new_file.xdata =  linspace(eval(x_start),eval(x_stop),datapoints)
    equation = equation.replace("X", "new_file.xdata")
    equation = str(equation.replace("^", "**"))
    equation = str(equation.replace(",", "."))  
    equation += " + new_file.xdata*0"
    new_file.ydata = eval(equation)
    new_file.xdata = ndarray.tolist(new_file.xdata)
    new_file.filename = name
    new_file.linestyle_selected = self.preferences.config["plot_selected_linestyle"]
    new_file.linestyle_unselected = self.preferences.config["plot_unselected_linestyle"]
    new_file.selected_line_thickness = self.preferences.config["selected_linewidth"]
    new_file.unselected_line_thickness = self.preferences.config["unselected_linewidth"]
    new_file.selected_markers = self.preferences.config["plot_selected_markers"]
    new_file.unselected_markers = self.preferences.config["plot_unselected_markers"]
    new_file.selected_marker_size = self.preferences.config["plot_selected_marker_size"]
    new_file.unselected_marker_size = self.preferences.config["plot_unselected_marker_size"]
    return new_file

@Gtk.Template(resource_path="/se/sjoerd/DatMan/add_equation_window.ui")
class AddEquationWindow(Adw.Window):
    __gtype_name__ = "AddEquationWindow"
    add_equation_confirm_button = Gtk.Template.Child()
    step_size_entry = Gtk.Template.Child()
    X_stop_entry = Gtk.Template.Child()
    X_start_entry = Gtk.Template.Child()
    equation_entry = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.step_size_entry.set_text(parent.preferences.config["addequation_step_size"])
        self.X_start_entry.set_text(parent.preferences.config["addequation_X_start"])
        self.X_stop_entry.set_text(parent.preferences.config["addequation_X_stop"])
        self.equation_entry.set_text(parent.preferences.config["addequation_equation"])        

        style_context = self.add_equation_confirm_button.get_style_context()
        style_context.add_class("suggested-action")
