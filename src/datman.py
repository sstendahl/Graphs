from gi.repository import Gtk, Gdk, Gio, GObject, Adw
import gi
import re
from .plotting_tools import PlotWidget
from . import plotting_tools
import numpy as np
from . import samplerow
from .data import Data
from matplotlib import colors
from . import colorpicker
from . import toolbar
from matplotlib.backends.backend_gtk4 import (
    NavigationToolbar2GTK4 as NavigationToolbar)

gi.require_version('Adw', '1')
gi.require_version('Gtk', '4.0')

def get_theme_color(self):
    win = self.props.active_window
    styles = win.get_style_context()
    rgba = styles.lookup_color('theme_bg_color')[1]
    rgba_tuple = (round(rgba.red*255), round(rgba.green*255), round(rgba.blue*255), round(rgba.alpha*255))
    color_hex = '#{:02x}{:02x}{:02x}'.format(*rgba_tuple)
    return color_hex

def get_dict_by_value(dictionary, value):
    new_dict = dict((v, k) for k, v in dictionary.items())
    if value == "none":
        return "none"
    return new_dict[value]


def open_selection(self, files, from_dictionary = False):
    if self.highlight is not None:
        plotting_tools.hide_highlight(self)
    if from_dictionary:
        for key, item in self.datadict.items():
            if item is not None:
                if self.item_rows[key].selected == True:
                    linewidth = self.preferences.config["selected_linewidth"]
                    linestyle = self.preferences.config["plot_selected_linestyle"]
                    marker = self.preferences.config["plot_selected_markers"]
                    marker_size = self.preferences.config["plot_selected_marker_size"]
                else:
                    linewidth = self.preferences.config["unselected_linewidth"]
                    linestyle = self.preferences.config["plot_unselected_linestyle"]
                    marker = self.preferences.config["plot_unselected_markers"]
                    marker_size = self.preferences.config["plot_unselected_marker_size"]
                color = self.item_rows[key].color_picker.color

                plotting_tools.plot_figure(self, self.canvas, item.xdata,item.ydata, item.filename, linewidth = linewidth, linestyle=linestyle, color = color, marker = marker, marker_size = marker_size)
    else:
        for path in files:
            if path != "":
                item = get_data(path)
                filename = path.split("/")[-1]
                item.xdata_clipboard = [item.xdata]
                item.ydata_clipboard = [item.ydata]
                item.clipboard_pos = -1
                if filename not in self.datadict:
                    self.datadict[filename] = item
                    item.filename = filename
                    color = plotting_tools.get_next_color(self)
                    plotting_tools.plot_figure(self, self.canvas, item.xdata,item.ydata, item.filename, color)
                    add_sample_to_menu(self, filename, color)
        self.canvas.draw()
        plotting_tools.set_canvas_limits(self, self.canvas)
        select_top_row(self)
        turn_off_clipboard_buttons(self)

def turn_off_clipboard_buttons(self):
        win = self.props.active_window
        undo_button = win.undo_button
        redo_button = win.redo_button
        redo_button.set_sensitive(False)
        undo_button.set_sensitive(False)

def toggle_darkmode(shortcut, theme, widget, self):
    win = self.props.active_window
    if len(self.datadict) > 0:
        key = list(self.datadict.keys())[0]
        item = self.item_rows[key]
        item.set_css(item.get_css())
    plotting_tools.reload_plot(self)


def select_top_row(self):
    win = self.props.active_window
    key = list(self.datadict.keys())[0]
    item = self.item_rows[key]
    item.selected = True
    item.set_css_classes(['label_selected'])
    item.set_css(item.get_css())
    plotting_tools.refresh_plot(self)

def get_data(path):
    data = Data()
    seperator = "\t "
    data_array = [[], []]
    with (open(path, 'r')) as file:
        for line in file:
            line = line.strip()
            line = re.split('\s+', line)
            try:
                data_array[0].append(float(line[0]))
                data_array[1].append(float(line[1]))
            except ValueError:
                pass
    data.xdata = data_array[0]
    data.ydata = data_array[1]
    return data

def delete(widget, self, filename):
    layout = self.sample_box
    for key, item in self.item_rows.items():
        if key == filename:
            self.sample_box.remove(item)
    del self.item_rows[filename]
    del self.datadict[filename]

    if len(self.datadict) == 0:
        self.canvas.ax.get_legend().remove()
        self.canvas.ax.set_prop_cycle(None)


    for key, item in self.datadict.items():
        item.xdata_clipboard = [item.xdata]
        item.ydata_clipboard = [item.ydata]
        item.clipboard_pos = -1
    turn_off_clipboard_buttons(self)
    plotting_tools.refresh_plot(self)

def select_all(widget, _, self):
    for key, item in self.item_rows.items():
        item.selected = True
        item.set_css_classes(['label_selected'])
        item.set_css(item.css)
    plotting_tools.refresh_plot(self)


def select_none(widget, _, self):
    for key, item in self.item_rows.items():
        item.selected = False
        item.set_css_classes(['label_deselected'])
        item.set_css(item.css)
    plotting_tools.refresh_plot(self)

def create_rgba(r, g, b, a=1.0):
    res = Gdk.RGBA()
    res.red = r
    res.green = g
    res.blue = b
    res.alpha = a
    return res


def add_sample_to_menu(self, filename, color):
    win = self.props.active_window
    self.sample_box = win.sample_box
    row = samplerow.SampleBox(self, filename)
    row.gesture.connect("pressed", row.clicked, self)
    row.color_picker = colorpicker.ColorPicker(color)
    row.color_picker.set_hexpand(False)
    sample_box = row.sample_box
    sample_box.remove(sample_box.get_last_child())
    row.sample_box.append(row.color_picker)
    row.sample_box.append(row.delete_button)
    row.delete_button.connect("clicked", delete, self, filename)
    row.color_picker.connect("color-set", row.color_picker.on_color_set, self)
    max_length = int(35)
    if len(filename) > max_length:
        label = f"{filename[:max_length]}..."
    else:
        label = filename
    row.sample_ID_label.set_text(label)
    self.item_rows[filename] = row
    self.sample_box.append(row)

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
        print("YOOO")
        filename = list(self.datadict.values())[0].filename
        chooser.set_current_name(f"{filename}.txt")
    chooser.set_modal(True)
    chooser.connect("response", on_save_response, self)
    chooser.show()

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
        array = np.stack([xdata, ydata], axis=1)
        np.savetxt(filename, array, delimiter="\t")
    elif len(self.datadict) > 1:
        for key, item in self.datadict.items():
            xdata = item.xdata
            ydata = item.ydata
            filename = key
            array = np.stack([xdata, ydata], axis=1)
            np.savetxt(path + "/" + filename, array, delimiter="\t")

def open_file_dialog(widget, _, self):
     open_file_chooser = Gtk.FileChooserNative.new(
        title="Open new files",
        parent=self.props.active_window,
        action=Gtk.FileChooserAction.OPEN,
        accept_label="_Open",
    )
     open_file_chooser.set_modal(True)
     open_file_chooser.set_select_multiple(True)
     open_file_chooser.connect("response", on_open_response, self)
     open_file_chooser.show()

def on_open_response(dialog, response, self):
    files = []
    if response == Gtk.ResponseType.ACCEPT:
        for file in dialog.get_files():
            file_path = file.peek_path()
            filename = file_path.split("/")[-1]
            files.append(file_path)
        open_selection(self, files)
        self.define_highlight = None
        plotting_tools.define_highlight(self)
        win = self.props.active_window
        button = win.select_data_button
        if not button.get_active():
            self.highlight.set_visible(False)
            self.highlight.set_active(False)


def load_empty(self):
    win = self.props.active_window
    layout = win.drawing_layout
    xlabel = self.preferences.config["plot_X_label"]
    ylabel = self.preferences.config["plot_Y_label"]
    self.canvas = PlotWidget(parent = self, xlabel=xlabel, ylabel=ylabel)
    clear_layout(self)
    create_layout(self, self.canvas, layout)

def clear_layout(self):
    win = self.props.active_window
    layout = win.drawing_layout
    remove = True
    while remove == True:
        child = layout.get_first_child()
        if child is not None:
            layout.remove(child)
        else:
            remove = False

def create_layout(self, canvas, layout):
    self.toolbar = toolbar.GraphToolbar(canvas, self)
    layout.append(canvas)
    layout.append(self.toolbar)
