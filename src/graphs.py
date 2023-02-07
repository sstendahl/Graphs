# SPDX-License-Identifier: GPL-3.0-or-later
import gi
import os
import re
import numpy

from gi.repository import Gtk, Adw
from matplotlib.backends.backend_gtk4 import NavigationToolbar2GTK4 as NavigationToolbar

from . import plotting_tools, samplerow, colorpicker, utilities
from .plotting_tools import PlotWidget
from .data import Data

def get_theme_color(self):
    win = self.props.active_window
    styles = win.get_style_context()
    rgba = styles.lookup_color('theme_bg_color')[1]
    rgba_tuple = (round(rgba.red*255), round(rgba.green*255), round(rgba.blue*255), round(rgba.alpha*255))
    color_hex = '#{:02x}{:02x}{:02x}'.format(*rgba_tuple)
    return color_hex

def open_selection_from_dict(self):
    for key, item in self.datadict.items():
        if item is not None:
            if self.item_rows[key].check_button.get_active():
                linewidth = item.selected_line_thickness
                linestyle = item.linestyle_selected
                marker = item.selected_markers
                marker_size = item.selected_marker_size
            else:
                linewidth = item.unselected_line_thickness
                linestyle = item.linestyle_unselected
                marker = item.unselected_markers
                marker_size = item.unselected_marker_size
            color = self.item_rows[key].color_picker.color
            y_axis = item.plot_Y_position
            x_axis = item.plot_X_position
            plotting_tools.plot_figure(self, self.canvas, item.xdata,item.ydata, item.filename, linewidth = linewidth, linestyle=linestyle, color = color, marker = marker, marker_size = marker_size, y_axis = y_axis, x_axis = x_axis)

def open_selection_from_file(self, files, import_settings):
    for path in files:
        if path != "":
            try:
                item = get_data(self, path, import_settings)
                if item.xdata == []:
                    self.props.active_window.toast_overlay.add_toast(Adw.Toast(title=f"At least one data set could not be imported"))                    
                    continue
            except IndexError:
                self.props.active_window.toast_overlay.add_toast(Adw.Toast(title=f"Could not open data, the column index was out of range"))
                break
            except UnicodeDecodeError:
                self.props.active_window.toast_overlay.add_toast(Adw.Toast(title=f"Could not open data, wrong filetype"))
                break
            if item is not None:
                handle_duplicates = self.preferences.config["handle_duplicates"]
                if not handle_duplicates == "Add duplicates":
                    for key, item2 in self.datadict.items():
                        if item.filename == item2.filename:
                            if handle_duplicates == "Auto-rename duplicates":
                                item.filename = get_duplicate_filename(self, item.filename)
                            elif handle_duplicates == "Ignore duplicates":
                                self.props.active_window.toast_overlay.add_toast(Adw.Toast(title=f"Item \"{item.filename}\" already exists"))
                                return
                            elif handle_duplicates == "Override existing items":
                                y_axis = item.plot_Y_position
                                x_axis = item.plot_X_position
                                self.datadict[key] = item
                                plotting_tools.reload_plot(self)
                                return
                y_axis = item.plot_Y_position
                x_axis = item.plot_X_position
                self.datadict[item.id] = item
                item.color = plotting_tools.get_next_color(self)
                plotting_tools.plot_figure(self, self.canvas, item.xdata,item.ydata, item.filename, item.color, y_axis = y_axis, x_axis = x_axis)
                add_sample_to_menu(self, item.filename, item.color, item.id, select_item = True)
    self.canvas.draw()
    plotting_tools.set_canvas_limits_axis(self, self.canvas)
    plotting_tools.refresh_plot(self)
    enable_data_dependent_buttons(self, utilities.get_selected_keys(self))


def get_duplicate_filename(self, name):
    loop = True
    i = 0
    while loop:
        i += 1
        new_name = f"{name} ({i})"
        loop = False
        for key, item in self.datadict.items():
            if new_name == item.filename:
                loop = True
    return new_name

def toggle_darkmode(shortcut, theme, widget, self):
    if Adw.StyleManager.get_default().get_dark():
        self.plot_settings.plot_style = self.preferences.config["plot_style_dark"]
    else:
        self.plot_settings.plot_style = self.preferences.config["plot_style_light"]
    plotting_tools.reload_plot(self)


def select_item(self, key):
    item = self.item_rows[key]
    item.check_button.set_active(True)
    plotting_tools.refresh_plot(self)
    enable_data_dependent_buttons(self, utilities.get_selected_keys(self))

def get_data(self, path, import_settings):
    data_array = [[], []]
    i = 0
    with (open(path, 'r')) as file:
        for line in file:
            i += 1
            if i > import_settings["skip_rows"]:
                line = line.strip()
                data_line = re.split(str(import_settings["delimiter"]), line)
                if import_settings["separator"] == ",":
                    for index, value in enumerate(data_line):
                        data_line[index] = swap(value)
                try:
                    data_array[0].append(float(data_line[import_settings["column_x"]]))
                    data_array[1].append(float(data_line[import_settings["column_y"]]))
                    
                #If it finds non-numbers, it will raise a ValueError, this is the cue to 
                #start looking for headers
                except ValueError:
                    if import_settings["guess_headers"]:
                        #By default it will check for headers using at least two whitespaces
                        #as delimiter (often tabs), but if that doesn't work it will try
                        #the same delimiter as used for the data import itself
                        #The reasoning is that some people use tabs for the headers, but 
                        #e.g. commas for the data
                        try:
                            headers = re.split("\s{2,}", line)
                            self.plot_settings.xlabel = headers[import_settings["column_x"]]
                            self.plot_settings.ylabel = headers[import_settings["column_y"]]
                        except IndexError:
                            try:
                                headers = re.split(import_settings["delimiter"], line)
                                self.plot_settings.xlabel = headers[import_settings["column_x"]]
                                self.plot_settings.ylabel = headers[import_settings["column_y"]]
                            #If neither heuristic works, we just skip the headers
                            except IndexError:
                                pass
    data = Data(data_array[0], data_array[1])
    data.plot_Y_position = self.preferences.config["plot_Y_position"]
    data.plot_X_position = self.preferences.config["plot_X_position"]
    data = set_data_properties(self, path, data, import_settings)
    return data

def set_data_properties(self, path, data, import_settings):
    data.linestyle_selected = self.preferences.config["plot_selected_linestyle"]
    data.linestyle_unselected = self.preferences.config["plot_unselected_linestyle"]
    data.selected_line_thickness = self.preferences.config["selected_linewidth"]
    data.unselected_line_thickness = self.preferences.config["unselected_linewidth"]
    data.selected_markers = self.preferences.config["plot_selected_markers"]
    data.unselected_markers = self.preferences.config["plot_unselected_markers"]
    data.selected_marker_size = self.preferences.config["plot_selected_marker_size"]
    data.unselected_marker_size = self.preferences.config["plot_unselected_marker_size"]
    if import_settings["name"] != "" and import_settings["mode"] == "single":
        filename = import_settings["name"]
    else:
        filename = path.split("/")[-1]
        filename = os.path.splitext(filename)[0]
    data.filename = filename
    return data

def swap(str1):
    str1 = str1.replace(',', 'third')
    str1 = str1.replace('.', ', ')
    str1 = str1.replace('third', '.')
    return str1

def delete_selected(shortcut, _,  self):
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        delete(None, self, key)


def delete(widget,  self, id, give_toast = True):
    layout = self.list_box
    for key, item in self.sample_menu.items():
        if key == id:
            layout.remove(item)
    filename = self.datadict[id].filename
    del self.item_rows[id]
    del self.datadict[id]
    if give_toast:
        self.props.active_window.toast_overlay.add_toast(Adw.Toast(title=f"Deleted {filename}"))

    if len(self.datadict) == 0:
        self.canvas.ax.legend().remove()
        self.canvas.ax.set_prop_cycle(None)
        layout.set_visible(False)

    reset_clipboard(self)
    plotting_tools.refresh_plot(self)
    enable_data_dependent_buttons(self, utilities.get_selected_keys(self))


def select_all(widget, _, self):
    for key, item in self.item_rows.items():
        item.check_button.set_active(True)
    plotting_tools.refresh_plot(self)
    enable_data_dependent_buttons(self, utilities.get_selected_keys(self))


def select_none(widget, _, self):
    for key, item in self.item_rows.items():
        item.check_button.set_active(False)
    plotting_tools.refresh_plot(self)
    enable_data_dependent_buttons(self, False)

def add_sample_to_menu(self, filename, color, id, select_item = False):
    win = self.main_window
    self.main_window.list_box.set_visible(True)
    self.list_box = win.list_box
    row = samplerow.SampleBox(self, filename, id)
    row.gesture.connect("released", row.clicked, self)
    row.color_picker = colorpicker.ColorPicker(color, parent=self)
    row.color_picker.set_hexpand(False)
    label = row.sample_ID_label
    if select_item:
        row.check_button.set_active(True)
    row.sample_box.insert_child_after(row.color_picker, row.sample_ID_label)
    row.check_button.connect("toggled", toggle_data, self, id)
    row.delete_button.connect("clicked", delete, self, id)
    self.item_rows[id] = row
    max_length = int(26)
    if len(filename) > max_length:
        label = f"{filename[:max_length]}..."
    else:
        label = filename
    row.sample_ID_label.set_text(label)
    self.list_box.append(row)
    self.sample_menu[id] = self.list_box.get_last_child()

def toggle_data(widget,  self, id):
    plotting_tools.refresh_plot(self)
    enable_data_dependent_buttons(self, utilities.get_selected_keys(self))

def save_file_dialog(self, documenttype="Text file (*.txt)"):
    def save_file_chooser(action):
        dialog = Gtk.FileChooserNative.new(
            title="Save files",
            parent=self.props.active_window,
            action=action,
            accept_label="_Save",
        )
        return dialog

    if len(self.datadict) == 1:
        chooser = save_file_chooser(Gtk.FileChooserAction.SAVE)
    elif len(self.datadict) > 1:
        chooser = save_file_chooser(Gtk.FileChooserAction.SELECT_FOLDER)

    if len(self.datadict) == 1:
        filename = list(self.datadict.values())[0].filename
        chooser.set_current_name(f"{filename}.txt")
    try:
        chooser.set_modal(True)
        chooser.connect("response", on_save_response, self)
        chooser.show()
    except UnboundLocalError:
        self.props.active_window.toast_overlay.add_toast(Adw.Toast(title=f"Could not open save dialog, make sure you have data opened"))


def on_save_response(dialog, response, self):
    files = []
    if response == Gtk.ResponseType.ACCEPT:
        path = dialog.get_file().peek_path()
        save_file(self, path)


def save_file(self, path):
    if len(self.datadict) == 1:
        for key, item in self.datadict.items():
            xdata = item.xdata
            ydata = item.ydata
        filename = path
        array = numpy.stack([xdata, ydata], axis=1)
        numpy.savetxt(str(filename), array, delimiter="\t")
    elif len(self.datadict) > 1:
        for key, item in self.datadict.items():
            xdata = item.xdata
            ydata = item.ydata
            filename = key
            array = numpy.stack([xdata, ydata], axis=1)
            if os.path.exists(f"{path}/{filename}.txt"):
                numpy.savetxt(str(path + "/" + filename) + " (copy).txt", array, delimiter="\t")
            else:
                numpy.savetxt(str(path + "/" + filename) + ".txt", array, delimiter="\t")


def open_file_dialog(widget, _, self, import_settings = None):
    open_file_chooser = Gtk.FileChooserNative.new(
        title="Open new files",
        parent=self.props.active_window,
        action=Gtk.FileChooserAction.OPEN,
        accept_label="_Open",
    )

    open_file_chooser.set_modal(True)
    open_file_chooser.set_select_multiple(True)
    open_file_chooser.connect("response", on_open_response, self, import_settings)
    open_file_chooser.show()

def get_import_settings(self):
    import_settings = dict()
    import_settings["delimiter"] = self.preferences.config["import_delimiter"]
    import_settings["guess_headers"] = self.preferences.config["guess_headers"]
    import_settings["separator"] = self.preferences.config["import_separator"]
    import_settings["skip_rows"] = int(self.preferences.config["import_skip_rows"])
    import_settings["column_x"] = int(self.preferences.config["import_column_x"])
    import_settings["column_y"] = int(self.preferences.config["import_column_y"])
    import_settings["name"] = ""
    return import_settings

def on_open_response(dialog, response, self, import_settings):
    files = []
    if response == Gtk.ResponseType.ACCEPT:
        for file in dialog.get_files():
            file_path = file.peek_path()
            filename = file_path.split("/")[-1]
            files.append(file_path)

        if import_settings is None:
            import_settings = get_import_settings(self)
        if len(dialog.get_files()) > 1:
            import_settings["mode"] = "multiple"
        elif len(dialog.get_files()) == 1:
            import_settings["mode"] = "single"

        open_selection_from_file(self, files, import_settings)


def load_empty(self):
    win = self.main_window
    xlabel = self.plot_settings.xlabel
    ylabel = self.plot_settings.ylabel
    self.canvas = PlotWidget(parent = self, xlabel=xlabel, ylabel=ylabel)
    self.dummy_toolbar = NavigationToolbar(self.canvas)
    win.toast_overlay.set_child(self.canvas)

def disable_clipboard_buttons(self):
    win = self.main_window
    win.redo_button.set_sensitive(False)
    win.undo_button.set_sensitive(False)

def reset_clipboard(self):
    for key, item in self.datadict.items():
        item.xdata_clipboard = [item.xdata]
        item.ydata_clipboard = [item.ydata]
        item.clipboard_pos = -1
    disable_clipboard_buttons(self)

def enable_data_dependent_buttons(self, enabled):
    win = self.main_window

    dependent_buttons = [
    win.shift_vertically_button,
    win.translate_x_button,
    win.translate_y_button,
    win.multiply_x_button,
    win.multiply_y_button,
    win.smooth_button,
    win.fourier_button,
    win.inverse_fourier_button,
    win.normalize_button,
    win.center_data_button,
    win.derivative_button,
    win.integral_button,
    win.transform_data_button,
    win.combine_data_button,
    ]

    for button in dependent_buttons:
        button.set_sensitive(enabled)
