from gi.repository import Gtk, Gio, GObject, Adw
import gi
import re
import numpy as np
from .plotting_tools import PlotWidget
from . import plotting_tools, datman, utilities
from scipy import integrate
from .data import Data
from matplotlib.backends.backend_gtk4 import (
    NavigationToolbar2GTK4 as NavigationToolbar)

gi.require_version('Adw', '1')
gi.require_version('Gtk', '4.0')

def save_data(widget, _, self):
    """
    Open the save file dialog.
    """
    delete_selected_data(self)
    datman.save_file_dialog(self)

def add_to_clipboard(self):
    """
    Add data to the clipboard, is performed whenever an action is performed.
    Appends the latest state to the clipboard.
    """
    undo_button = self.props.active_window.undo_button
    undo_button.set_sensitive(True)
    
    #If a couple of redo's were performed previously, it deletes the clipboard
    #data that is located after the current clipboard position and disables the
    #redo button
    for key, item in self.datadict.items():
        delete_lists = - item.clipboard_pos - 1
        for index in range(delete_lists):
            del item.xdata_clipboard[-1]
            del item.ydata_clipboard[-1]
        if delete_lists != 0:
            redo_button = self.props.active_window.redo_button
            redo_button.set_sensitive(False)

        item.clipboard_pos = -1
        item.xdata_clipboard.append(item.xdata)
        item.ydata_clipboard.append(item.ydata)

def undo(widget, shortcut, self):
    """
    Undo an action, moves the clipboard position backwards by one and changes
    the dataset to the state before the previous action was performed
    """
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
    """
    Redo an action, moves the clipboard position forwards by one and changes the 
    dataset to the state before the previous action was undone
    """
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
    """
    Delete the data sets that have the _selected suffix on their ID.
    This is the separate dataset that is created whenever part of the data set
    falls within a span, not the parent dataset itself.
    """
    key_list = []
    for key in self.datadict:
        if key.endswith("_selected"):
            key_list.append(key)
    for key in key_list:
        del (self.datadict[key])

def pick_data_selection(self, item, startx, stopx):
    """
    Checks for a given item if it is within the selected span. If it is, it 
    returns the part of the data that is within the span.
    """
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
    """
    Sort x and y-coordinates such that the x-data is continiously increasing
    Takes in x, and y coordinates of that array, and returns the sorted variant
    """
    bar_list = {"x": x, "y": y}
    sorted = sort_bar(bar_list)
    return sorted["x"], sorted["y"]

def sort_bar(bar_list):
    """
    Sort x and y-coordinates such that the x-data is continiously increasing
    Takes in one bar list, sorts it and returns the sorted version
    """
    sorted_x = []
    sorted_x.extend(bar_list['x'])
    sorted_x.sort()
    sorted_y = []
    for x in sorted_x:
        sorted_y.append(bar_list['y'][bar_list['x'].index(x)])
    return {"x": sorted_x, "y": sorted_y}

def cut_data(widget, _, self):
    """
    Cut selected data over the span that is selected
    """
    win = self.props.active_window
    button = win.select_data_button
    if button.get_active():
        if select_data(self): #If select_data ran succesfully
            for key, item in self.datadict.items():
                if item is None:
                    continue
                xdata = item.xdata
                ydata = item.ydata
                #Create empty arrays that will be equal to the new cut data 
                new_x = []
                new_y = []
                
                #If our item is among the selected samples, we will cut those
                if f"{key}_selected" in self.datadict:
                    selected_item = self.datadict[f"{key}_selected"]
                    if selected_item == None:
                        continue
                    for index, (valuex, valuey) in enumerate(zip(xdata, ydata)):
                        #Appends the values that are within the selected span
                        if valuex < min(selected_item.xdata) or valuex > max(selected_item.xdata):
                            new_x.append(valuex)
                            new_y.append(valuey)
                    item.xdata = new_x
                    item.ydata = new_y
            delete_selected_data(self)
            add_to_clipboard(self)
            plotting_tools.refresh_plot(self, set_limits = False)

def select_data(self):
    """
    Select data that is highlighted by the span
    Basically just creates new data_sets with the key "_selected" appended
    """
    #First delete previously selected data
    delete_selected_data(self)
    selected_dict = {}
    selected_keys = utilities.get_selected_keys(self)

    for key in selected_keys:
        item = self.datadict[key]
        highlight = self.highlight
        startx = min(highlight.extents)
        stopx = max(highlight.extents)
        
        #Selection is different for bottom and top axis. The span selector takes
        #the top axis coordinates. So for the data that uses the bottom axis as
        #x-axis coordinates, the coordinates first needs to be converted.
        if item.plot_X_position == "bottom":
            xrange_bottom = max(self.canvas.ax.get_xlim()) - min(self.canvas.ax.get_xlim())
            xrange_top = max(self.canvas.top_left_axis.get_xlim()) - min(self.canvas.top_left_axis.get_xlim())
            startx = ((startx - min(self.canvas.top_left_axis.get_xlim())) / xrange_top) * xrange_bottom + min(self.canvas.ax.get_xlim())
            stopx = ((stopx - min(self.canvas.top_left_axis.get_xlim())) / xrange_top) * xrange_bottom + min(self.canvas.ax.get_xlim())
        
        #Select data
        if not ((startx < min(item.xdata) and stopx < min(item.xdata)) or (startx > max(item.xdata))):
            selected_data = pick_data_selection(self, item, startx, stopx)
            selected_dict[f"{key}_selected"] = selected_data
        if (startx < min(item.xdata) and stopx < min(item.xdata)) or (startx > max(item.xdata)):
            delete_selected_data(self)
        #Update the dataset to include the selected data, only if we actually
        #managed to select data.
        if len(selected_dict) > 0:
            self.datadict.update(selected_dict)
    return True

def get_derivative(widget, shortcut, self):
    """
    Calculate derivative of all selected data
    """
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        item = self.datadict[key]
        x = np.array(item.xdata)
        y = np.array(item.ydata)
        dy_dx = np.gradient(y, x)
        item.ydata =  dy_dx.tolist()
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def get_integral(widget, shortcut, self):
    """
    Calculate indefinite integral of all selected data
    """
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        item = self.datadict[key]
        x = np.array(item.xdata)
        y = np.array(item.ydata)
        F = integrate.cumtrapz(y, x, initial=0)
        item.ydata =  F.tolist()
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def get_inverse_fourier(widget, shortcut, self):
    """
    Perform Inverse Fourier transformation on all selected data
    """
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        item = self.datadict[key]
        x = np.array(item.xdata)
        y = np.array(item.ydata)
        y_fourier = np.fft.ifft(y)
        x_fourier = np.fft.fftfreq(len(x), x[1] - x[0])
        y_fourier = [value.real for value in y_fourier]
        x_fourier, y_fourier = sort_data(x_fourier.tolist(), y_fourier)
        item.ydata =  y_fourier
        item.xdata = x_fourier
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def get_fourier(widget, shortcut, self):
    """
    Perform Fourier transformation on all selected data
    """
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        item = self.datadict[key]
        x = np.array(item.xdata)
        y = np.array(item.ydata)
        y_fourier = np.fft.fft(y)
        x_fourier = np.fft.fftfreq(len(x), x[1] - x[0])
        y_fourier = [value.real for value in y_fourier]
        
        x_fourier, y_fourier = sort_data(x_fourier.tolist(), y_fourier)
        item.ydata =  y_fourier
        item.xdata = x_fourier
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def smoothen_data(widget, shortcut, self):
    """
    Smoothen y-data. If logscale is true, it smoothenes on the log scale
    instead.
    """
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

def smooth(y_data, box_points):
    """
    Smoothen data, takes the y_array and the box-points, which neighbouring
    values are used for smoothening. Returns smoothened array
    """
    box = np.ones(box_points) / box_points
    y_smooth = np.convolve(y_data, box, mode="same")
    return y_smooth

def shift_vertically(shortcut, _, self):
    """
    Shifts data vertically with respect to each other
    By default it scales linear data by 1.5 times the total span of the 
    ydata, and log data by a factor of 10000.
    """
    shifter = 1
    shift_value_log = 0
    shift_value_linear = 0
        
    for key, item in self.datadict.items():
        item.ydata = normalize(item.ydata)
        ymin = min(x for x in item.ydata if x != 0)
        ymax = max(x for x in item.ydata if x != 0)
        shift_value_linear += 1.5*(ymax - ymin)
        shift_value_log += 5*10**(np.log10(ymax/ymin))
        #Check which axes the data is on, so it can choose the appropriate
        #scaling (log/linear)
        if item.plot_Y_position == "left":
            if self.plot_settings.yscale == "log":
                item.ydata = [value * shifter for value in item.ydata]
            if self.plot_settings.yscale == "linear":
                item.ydata = [value + shift_value_linear for value in item.ydata]
        if item.plot_Y_position == "right":
            if self.plot_settings.right_scale == "log":
                item.ydata = [value * shifter for value in item.ydata]
            if self.plot_settings.right_scale == "linear":
                item.ydata = [value + shift_value_linear for value in item.ydata]
                
        shifter *= shift_value_log
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def translate_x(shortcut, _, self):
    """
    Translate all selected data on the x-axis
    Amount to be shifted is equal to the value in the translate_x entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
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
    """
    Translate all selected data on the y-axis
    Amount to be shifted is equal to the value in the translate_y entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
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
    """
    Multiply all selected data on the x-axis
    Amount to be shifted is equal to the value in the multiply_y entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
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
    """
    Multiply all selected data on the y-axis
    Amount to be shifted is equal to the value in the multiply_y entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
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
    """
    Normalize all selected data
    """
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        self.datadict[key].ydata = normalize(self.datadict[key].ydata)
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def normalize(ydata):
    """
    Normalize input.
    Divides each value in an array by the maximum value in the array
    """
    max_y = max(ydata)
    new_y = [value / max_y for value in ydata]
    return new_y

def center_data(shortcut, _, self):
    """
    Center all selected data
    Depending on the key, will center either on the middle coordinate, or on
    the maximum value of the data
    """
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        if self.preferences.config["action_center_data"] == "Center at maximum Y value":
            self.datadict[key].xdata = center_data_max_Y(self.datadict[key].xdata, self.datadict[key].ydata)
        elif self.preferences.config["action_center_data"] == "Center at middle coordinate":
            self.datadict[key].xdata = center_data_middle(self.datadict[key].xdata)
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)


def center_data_max_Y(xdata, ydata):
    """
    Center data on the maximum y value, takes in x array and y array.
    Centers the x-data at index where the y-data has its maximum
    """
    max_value = max(ydata)
    middle_index = ydata.index(max_value)
    middle_value = xdata[middle_index]
    xdata = [coordinate - middle_value for coordinate in xdata]
    return xdata

def center_data_middle(xdata):
    """
    Center data on the middle value, takes in x array.
    Translates the x-array by the middle point of the array, so that this
    middle point lies in the center
    """
    middle_value = (min(xdata) + max(xdata)) / 2
    xdata = [coordinate - middle_value for coordinate in xdata]
    return xdata
