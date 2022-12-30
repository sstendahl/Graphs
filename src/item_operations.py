from gi.repository import Gtk, Gio, GObject, Adw
import gi
import re
import numpy as np
from .plotting_tools import PlotWidget
from . import plotting_tools, datman, utilities
from .data import Data
from matplotlib.backends.backend_gtk4 import (
    NavigationToolbar2GTK4 as NavigationToolbar)

gi.require_version('Adw', '1')
gi.require_version('Gtk', '4.0')

def save_data(widget, _, self):
    delete_selected_data(self)
    datman.save_file_dialog(self)

def get_selected_keys(self):
    selected_keys = []
    for key, item in self.item_rows.items():
        if item.selected == True:
            selected_keys.append(item.filename)
    return selected_keys

def add_to_clipboard(self):
    undo_button = self.props.active_window.undo_button
    undo_button.set_sensitive(True)
    for key, item in self.datadict.items():
        delete_lists = - item.clipboard_pos - 1
        for index in range(delete_lists):
            del item.xdata_clipboard[-1]
            del item.ydata_clipboard[-1]

        item.clipboard_pos = -1
        item.xdata_clipboard.append(item.xdata)
        item.ydata_clipboard.append(item.ydata)

def undo(widget, shortcut, self):
    undo_button = self.props.active_window.undo_button
    redo_button = self.props.active_window.redo_button
    for key, item in self.datadict.items():
        if abs(item.clipboard_pos) < len(item.xdata_clipboard):
            redo_button.set_sensitive(True)
            item.clipboard_pos -= 1
            item.xdata = item.xdata_clipboard[item.clipboard_pos]
            item.ydata = item.ydata_clipboard[item.clipboard_pos]
    if abs(item.clipboard_pos) >= len(item.xdata_clipboard):
        undo_button.set_sensitive(False)
    plotting_tools.refresh_plot(self)

def redo(widget, shortcut, self):
    undo_button = self.props.active_window.undo_button
    redo_button = self.props.active_window.redo_button
    for key, item in self.datadict.items():
        if item.clipboard_pos < 0:
            undo_button.set_sensitive(True)
            item.clipboard_pos += 1
            item.xdata = item.xdata_clipboard[item.clipboard_pos]
            item.ydata = item.ydata_clipboard[item.clipboard_pos]
    if item.clipboard_pos >= -1:
        redo_button.set_sensitive(False)
    plotting_tools.refresh_plot(self)


def delete_selected_data(self):
    key_list = []
    for key in self.datadict:
        if key.endswith("_selected"):
            key_list.append(key)
    for key in key_list:
        del (self.datadict[key])

def pick_data_selection(self, item, startx, stopx):
    xdata = item.xdata
    ydata = item.ydata
    xdata, ydata = sort_data(xdata, ydata)
    start_index = 0
    stop_index = len(xdata)
    found_start = False
    found_stop = False
    for index, value in enumerate(xdata):
        if value > startx and not found_start:
            start_index = index
            found_start = True
        if value > stopx and not found_stop:
            stop_index = index
            found_stop = True
    selected_data = Data()
    selected_data.xdata = xdata[start_index:stop_index]
    selected_data.ydata = ydata[start_index:stop_index]
    if len(selected_data.xdata) > 0 and (found_start or found_stop) == True:
        return selected_data

def sort_data(x, y):
    bar_list = {"x": x, "y": y}
    sorted = sort_bar(bar_list)
    return sorted["x"], sorted["y"]

def sort_bar(bar_list):
    sorted_x = []
    sorted_x.extend(bar_list['x'])
    sorted_x.sort()
    sorted_y = []
    for x in sorted_x:
        sorted_y.append(bar_list['y'][bar_list['x'].index(x)])
    return {"x": sorted_x, "y": sorted_y}



def select_data(self):
    delete_selected_data(self)
    selected_dict = {}
    selected_keys = utilities.get_selected_keys(self)

    for key in selected_keys:
        item = self.datadict[key]
        highlight = self.highlight
        startx = min(highlight.extents)
        stopx = max(highlight.extents)
        if item.plot_X_position == "bottom":
            xrange_bottom = max(self.canvas.ax.get_xlim()) - min(self.canvas.ax.get_xlim())
            xrange_top = max(self.canvas.top_left_axis.get_xlim()) - min(self.canvas.top_left_axis.get_xlim())
            startx = (xrange_bottom / xrange_top)*startx + min(self.canvas.ax.get_xlim())
            stopx = (xrange_bottom / xrange_top)*stopx + min(self.canvas.ax.get_xlim())
        if not ((startx < min(item.xdata) and stopx < min(item.xdata)) or (startx > max(item.xdata))):
            selected_data = pick_data_selection(self, item, startx, stopx)
            selected_dict[f"{key}_selected"] = selected_data
        if (startx < min(item.xdata) and stopx < min(item.xdata)) or (startx > max(item.xdata)):
            delete_selected_data(self)

        if len(selected_dict) > 0:
            self.datadict.update(selected_dict)
    return True

def cut_data(widget, _, self):
    win = self.props.active_window
    button = win.select_data_button
    if button.get_active():
        if select_data(self):
            for key, item in self.datadict.items():
                if item is None:
                    continue
                xdata = item.xdata
                ydata = item.ydata
                new_x = []
                new_y = []
                if f"{key}_selected" in self.datadict:
                    selected_item = self.datadict[f"{key}_selected"]
                    if selected_item == None:
                        continue
                    for index, (valuex, valuey) in enumerate(zip(xdata, ydata)):
                        if valuex < min(selected_item.xdata) or valuex > max(selected_item.xdata):
                            new_x.append(valuex)
                            new_y.append(valuey)
                    item.xdata = new_x
                    item.ydata = new_y
            delete_selected_data(self)
            add_to_clipboard(self)
            plotting_tools.refresh_plot(self, set_limits = False)


def smoothen_data(widget, shortcut, self):
    selected_keys = utilities.get_selected_keys(self)
    logscale = False
    for key in selected_keys:
        ydata = self.datadict[key].ydata
        if logscale:
            ydata = [np.log(value) for value in ydata]
            ydata = smooth(ydata, 4)
            ydata = np.exp(ydata)
        else:
            ydata = smooth(ydata, 4)
        self.datadict[key].ydata = ydata
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def smooth(y, box_points):
    box = np.ones(box_points) / box_points
    y_smooth = np.convolve(y, box, mode="same")
    return y_smooth

def shift_vertically(shortcut, _, self):
    shifter = 1
    shift_value = 10000
    for key, item in self.datadict.items():
        item.ydata = [value * shifter for value in item.ydata]
        shifter *= shift_value
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def translate_x(shortcut, _, self):
    win = self.props.active_window
    try:
        offset = float(win.translate_x_entry.get_text())
    except ValueError:
        win.toast_overlay.add_toast(Adw.Toast(title=f"Unable to do translation, make sure to enter a valid number"))
        print("Unable to do translation, make sure to enter a valid number")
        offset = 0
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        self.datadict[key].xdata = [value + offset for value in self.datadict[key].xdata]
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def translate_y(shortcut, _, self):
    win = self.props.active_window
    try:
        offset = float(win.translate_y_entry.get_text())
    except ValueError:
        print("Unable to do translation, make sure to enter a valid number")
        offset = 0
        win.toast_overlay.add_toast(Adw.Toast(title=f"Unable to do translation, make sure to enter a valid number"))
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        self.datadict[key].ydata = [value + offset for value in self.datadict[key].ydata]
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def multiply_x(shortcut, _, self):
    win = self.props.active_window
    try:
        multiplier = float(win.multiply_x_entry.get_text())
    except ValueError:
        win.toast_overlay.add_toast(Adw.Toast(title=f"Unable to do multiplication, make sure to enter a valid number"))
        print("Unable to do multiplication, make sure to enter a valid number")
        multiplier = 1
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        self.datadict[key].xdata = [value * multiplier for value in self.datadict[key].xdata]
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def multiply_y(shortcut, _, self):
    win = self.props.active_window
    try:
        multiplier = float(win.multiply_y_entry.get_text())
    except ValueError:
        win.toast_overlay.add_toast(Adw.Toast(title=f"Unable to do multiplication, make sure to enter a valid number"))
        print("Unable to do multiplication, make sure to enter a valid number")
        multiplier = 1
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        self.datadict[key].ydata = [value * multiplier for value in self.datadict[key].ydata]
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)


def normalize_data(shortcut, _, self):
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        self.datadict[key].ydata = normalize(self.datadict[key].ydata)
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def normalize(ydata):
    max_y = max(ydata)
    new_y = [value / max_y for value in ydata]
    return new_y

def center_data(shortcut, _, self):
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        if self.preferences.config["center_data"] == "Center at maximum Y value":
            self.datadict[key].xdata = center_data_max_Y(self.datadict[key].xdata, self.datadict[key].ydata)
        elif self.preferences.config["center_data"] == "Center at middle coordinate":
            self.datadict[key].xdata = center_data_middle(self.datadict[key].xdata, self.datadict[key].ydata)
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)


def center_data_max_Y(xdata, ydata):
    max_value = max(ydata)
    middle_index = ydata.index(max_value)
    middle_value = xdata[middle_index]
    xdata = [coordinate - middle_value for coordinate in xdata]
    return xdata

def center_data_middle(xdata, ydata):
    middle_value = (min(xdata) + max(xdata)) / 2
    xdata = [coordinate - middle_value for coordinate in xdata]
    return xdata



