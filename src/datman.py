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

def open_selection(self, files, from_dictionary = False):
    if from_dictionary:
        for key, item in self.datadict.items():
            if item is not None:
                if self.item_rows[key].selected == True:
                    linewidth = 3
                else:
                    linewidth = 1.5
                color = self.item_rows[key].color_picker.color
                plotting_tools.plot_figure(self, self.canvas, item.xdata,item.ydata, item.filename, linewidth = linewidth, color = color)
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
    max_length = int(45)
    if len(filename) > max_length:
        filename = f"{filename[:max_length]}..."
    row.sample_ID_label.set_text(filename)
    self.item_rows[filename] = row
    self.sample_box.append(row)

def save_file_dialog(self, documenttype="Text file (*.txt)"):
    if len(self.datadict) == 1:
        self._native = Gtk.FileChooserNative(
            title="Save files",
            action=Gtk.FileChooserAction.SAVE,
            accept_label="_Save",
            cancel_label="_Cancel",
        )
    elif len(self.datadict) > 1:
        self._native = Gtk.FileChooserNative(
        title="Save files",
        action=Gtk.FileChooserAction.OPEN,
        accept_label="_Save",
        cancel_label="_Cancel",
    )
    self._native.connect("response", on_save_response, self)
    self._native.show()

def on_save_response(dialog, response, self):
    files = []
    if response == Gtk.ResponseType.ACCEPT:
        path = dialog.get_file().peek_path()
        if len(self.datadict) > 1:
            file_name = path.split("/")[-1]
            path = path[0:-len(file_name)]
        save_file(self, path)


def save_file(self, path):
    if len(self.datadict) == 1:
        for key, item in self.datadict.items():
            xdata = item.xdata
            ydata = item.ydata
        filename = path
        if filename[-4:] != ".txt":
            filename = filename + ".txt"
        array = np.stack([xdata, ydata], axis=1)
        np.savetxt(filename, array, delimiter="\t")
    elif len(self.datadict) > 1:

        for key, item in self.datadict.items():
            xdata = item.xdata
            ydata = item.ydata
            filename = key
            filename = filename.split(".")[0]
            filename = f"{path}/{filename}_edited.txt"
            array = np.stack([xdata, ydata], axis=1)
            np.savetxt(filename, array, delimiter="\t")
    self._native = None

def open_file_dialog(widget, _, self):
     self._native = Gtk.FileChooserNative(
        title="Open new files",
        action=Gtk.FileChooserAction.OPEN,
        accept_label="_Open",
        cancel_label="_Cancel",
    )
     self._native.set_select_multiple(True)
     self._native.connect("response", on_open_response, self)
     self._native.show()

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
    self._native = None


def load_empty(self):
    win = self.props.active_window
    layout = win.drawing_layout
    self.canvas = PlotWidget(xlabel="X value", ylabel="Y Value")
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


