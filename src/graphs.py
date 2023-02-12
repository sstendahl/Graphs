# SPDX-License-Identifier: GPL-3.0-or-later
import os
import numpy

from gi.repository import Gtk, Adw
from . import plotting_tools, samplerow, colorpicker, utilities, file_io
from .canvas import Canvas
from .data import Data
from .misc import DummyToolbar, ImportSettings

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

def open_files(self, files):
    import_settings = ImportSettings(self)
    if len(files) > 1:
        import_settings.mode = "multiple"
    elif len(files) == 1:
        import_settings.mode = "single"
    for file in files:
        path = file.peek_path()
        if path != "":
            try:
                import_settings.path = path
                item = file_io.get_data(self, import_settings)
                if item.xdata == []:
                    self.main_window.toast_overlay.add_toast(Adw.Toast(title=f"At least one data set could not be imported"))
                    continue
            except IndexError:
                self.main_window.toast_overlay.add_toast(Adw.Toast(title=f"Could not open data, the column index was out of range"))
                break
            except UnicodeDecodeError:
                self.main_window.toast_overlay.add_toast(Adw.Toast(title=f"Could not open data, wrong filetype"))
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
                self.datadict[item.key] = item
                item.color = plotting_tools.get_next_color(self)
                plotting_tools.plot_figure(self, self.canvas, item.xdata,item.ydata, item.filename, item.color, y_axis = y_axis, x_axis = x_axis)
                add_sample_to_menu(self, item.filename, item.color, item.key, select_item = True)
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
        self.main_window.no_data_label_box.set_visible(True)

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

def add_sample_to_menu(self, filename, color, key, select_item = False):
    win = self.main_window
    win.list_box.set_visible(True)
    win.no_data_label_box.set_visible(False)
    self.list_box = win.list_box
    row = samplerow.SampleBox(self, filename, key)
    row.gesture.connect("released", row.clicked, self)
    row.color_picker = colorpicker.ColorPicker(color, key, parent=self)
    row.color_picker.set_hexpand(False)
    label = row.sample_ID_label
    if select_item:
        row.check_button.set_active(True)
    row.sample_box.insert_child_after(row.color_picker, row.sample_ID_label)
    row.check_button.connect("toggled", toggle_data, self)
    row.delete_button.connect("clicked", delete, self, key)
    self.item_rows[key] = row
    max_length = int(26)
    if len(filename) > max_length:
        label = f"{filename[:max_length]}..."
    else:
        label = filename
    row.sample_ID_label.set_text(label)
    self.list_box.append(row)
    self.sample_menu[key] = self.list_box.get_last_child()
    
def toggle_data(widget,  self):
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
        chooser.connect("response", on_save_response, self, False)
        chooser.show()
    except UnboundLocalError:
        self.props.active_window.toast_overlay.add_toast(Adw.Toast(title=f"Could not open save dialog, make sure you have data opened"))


def on_save_response(dialog, response, self, project):
    if response == Gtk.ResponseType.ACCEPT:
        path = dialog.get_file().peek_path()
        if project:
            file_io.save_project(self, path)
        else:
            file_io.save_file(self, path)

def save_project_dialog(widget, _, self, documenttype="Graphs Project (*)"):
    def save_project_chooser(action):
        dialog = Gtk.FileChooserNative.new(
            title="Save files",
            parent=self.props.active_window,
            action=action,
            accept_label="_Save",
        )
        return dialog

    chooser = save_project_chooser(Gtk.FileChooserAction.SAVE)
    chooser.set_modal(True)
    chooser.connect("response", on_save_response, self, True)
    chooser.show()


def open_file_dialog(widget, _, self, open_project):
    open_file_chooser = Gtk.FileChooserNative.new(
        title="Open new files",
        parent=self.props.active_window,
        action=Gtk.FileChooserAction.OPEN,
        accept_label="_Open",
    )
    open_file_chooser.set_modal(True)
    open_file_chooser.set_select_multiple(open_project)
    open_file_chooser.connect("response", on_open_response, self, open_project)
    open_file_chooser.show()

def on_open_response(dialog, response, self, project):
    if response == Gtk.ResponseType.ACCEPT:
        if(project):
            file_io.load_project(self, dialog.get_files())
        else:
            open_files(self, dialog.get_files())

def create_data_from_project(self, new_dictionary):
    """
    Creates self.datadict using a new dictionary.
    This function uses new dictionary, which contains old Data objects in order to 
    create a new self.datadict dictionary, with new Data objects.
    It sets all matching attributes that exist in the old data set to the new data set. 
    Attributes that were removed and no longer used are not copied over, and will therefore
    revert to the default value.
    """
    self.datadict = dict()
    for key, item in new_dictionary.items():
        xdata = item.xdata
        ydata = item.ydata
        self.datadict[item.key] = Data(self, xdata, ydata)
        for attribute in self.datadict[item.key].__dict__:
            if hasattr(item, attribute):
                setattr(self.datadict[item.key], attribute, getattr(item, attribute))

def set_attributes(new_object, template):
    """
    Sets the attributes of `new_object` to match those of `template`.
    This function sets the attributes of `new_object` to the values of the attributes in `template` if they don't already exist in `new_object`. 
    Additionally, it removes any attributes from `new_object` that are not present in `template`.
    """
    for attribute in template.__dict__:
        if not hasattr(new_object, attribute):
            setattr(new_object, attribute, getattr(template, attribute))
    for attribute in new_object.__dict__:
        if not hasattr(template, attribute):
            delattr(new_object, attr)

def load_empty(self):
    win = self.main_window
    xlabel = self.plot_settings.xlabel
    ylabel = self.plot_settings.ylabel
    self.canvas = Canvas(parent = self, xlabel=xlabel, ylabel=ylabel)
    for axis in [self.canvas.right_axis, self.canvas.top_left_axis, self.canvas.top_right_axis]:
        axis.get_xaxis().set_visible(False)
        axis.get_yaxis().set_visible(False)    
    self.dummy_toolbar = DummyToolbar(self.canvas)
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
