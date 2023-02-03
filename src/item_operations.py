# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gtk, Gio, GObject, Adw
import gi
import re
import numpy as np
from .plotting_tools import PlotWidget
from . import plotting_tools, graphs, utilities
from scipy import integrate
from .data import Data
from .utilities import InteractionMode
from matplotlib.backends.backend_gtk4 import (
    NavigationToolbar2GTK4 as NavigationToolbar)

gi.require_version('Adw', '1')
gi.require_version('Gtk', '4.0')

def save_data(widget, _, self):
    """
    Open the save file dialog.
    """
    delete_selected_data(self)
    graphs.save_file_dialog(self)

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
        item.xdata_clipboard.append(item.xdata.copy())
        item.ydata_clipboard.append(item.ydata.copy())

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
            item.xdata = item.xdata_clipboard[item.clipboard_pos].copy()
            item.ydata = item.ydata_clipboard[item.clipboard_pos].copy()
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
            item.xdata = item.xdata_clipboard[item.clipboard_pos].copy()
            item.ydata = item.ydata_clipboard[item.clipboard_pos].copy()
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
        return selected_data, start_index, stop_index

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
    if self._mode == InteractionMode.SELECT:
        if select_data(self): #If select_data ran succesfully
            for key, item in self.datadict.items():
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
    start_stop = {}

    for key in selected_keys:
        item = self.datadict[key]
        highlight = self.highlight
        startx = min(highlight.extents)
        stopx = max(highlight.extents)
        start_index = 0
        stop_index = 0
        
        #Selection is different for bottom and top axis. The span selector takes
        #the top axis coordinates. So for the data that uses the bottom axis as
        #x-axis coordinates, the coordinates first needs to be converted.
        if item.plot_X_position == "bottom":
            xrange_bottom = max(self.canvas.ax.get_xlim()) - min(self.canvas.ax.get_xlim())
            xrange_top = max(self.canvas.top_left_axis.get_xlim()) - min(self.canvas.top_left_axis.get_xlim())
            #Run into issues if the range is different, so we calculate this by
            #getting what fraction of top axis is highlighted
            if self.canvas.top_left_axis.get_xscale() == "log":
                fraction_left_limit = get_fraction_at_value(min(highlight.extents), min(self.canvas.top_left_axis.get_xlim()), max(self.canvas.top_left_axis.get_xlim()))
                fraction_right_limit = get_fraction_at_value(max(highlight.extents), min(self.canvas.top_left_axis.get_xlim()), max(self.canvas.top_left_axis.get_xlim()))
            elif self.canvas.top_left_axis.get_xscale() == "linear":
                fraction_left_limit = (min(highlight.extents) - min(self.canvas.top_left_axis.get_xlim())) / (xrange_top)
                fraction_right_limit = (max(highlight.extents) - min(self.canvas.top_left_axis.get_xlim())) / (xrange_top)

            #Use the fraction that is higlighted on top to calculate to what
            #values this corresponds on bottom axis
            if self.canvas.ax.get_xscale() == "log":
                startx = get_value_at_fraction(fraction_left_limit, min(self.canvas.ax.get_xlim()), max(self.canvas.ax.get_xlim()))
                stopx = get_value_at_fraction(fraction_right_limit, min(self.canvas.ax.get_xlim()), max(self.canvas.ax.get_xlim()))
            elif self.canvas.ax.get_xscale() == "linear":
                startx = min(self.canvas.ax.get_xlim()) + xrange_bottom * fraction_left_limit
                stopx = min(self.canvas.ax.get_xlim()) + xrange_bottom * fraction_right_limit

        #If startx and stopx are not out of range, that is, if the sample data is within the highlight
        if not ((startx < min(item.xdata) and stopx < min(item.xdata)) or (startx > max(item.xdata))):
            selected_data, start_index, stop_index = pick_data_selection(self, item, startx, stopx)
            selected_dict[f"{key}_selected"] = selected_data
        if (startx < min(item.xdata) and stopx < min(item.xdata)) or (startx > max(item.xdata)):
            delete_selected_data(self)
        #Update the dataset to include the selected data, only if we actually
        #managed to select data.
        if len(selected_dict) > 0:
            self.datadict.update(selected_dict)
        start_stop[key] = [start_index, stop_index]
    return True, start_stop

def get_value_at_fraction(fraction, start, end):
    """
    Obtain the selected value of an axis given at which percentage (in terms of
    fraction) of the length this axis is selected given the start and end range
    of this axis
    """
    log_start = np.log10(start)
    log_end = np.log10(end)
    log_range = log_end - log_start
    log_value = log_start + log_range * fraction
    return pow(10, log_value)

def get_fraction_at_value(value, start, end):
    """
    Obtain the fraction of the total length of the selected axis a specific
    value corresponds to given the start and end range of the axis.
    """
    log_start = np.log10(start)
    log_end = np.log10(end)
    log_value = np.log10(value)
    log_range = log_end - log_start
    return (log_value - log_start) / log_range

def get_derivative(widget, shortcut, self):
    """
    Calculate derivative of all selected data
    """
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        if f"{key}_selected" in self.datadict:
            item = self.datadict[f"{key}_selected"]
        if self._mode != InteractionMode.SELECT:
            item = self.datadict[key]
        x = np.array(item.xdata)
        y = np.array(item.ydata)
        dy_dx = np.gradient(y, x)
        self.datadict[key].xdata = item.xdata
        self.datadict[key].ydata = dy_dx.tolist()
    add_to_clipboard(self)
    delete_selected_data(self)
    plotting_tools.refresh_plot(self)

def get_integral(widget, shortcut, self):
    """
    Calculate indefinite integral of all selected data
    """
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        if f"{key}_selected" in self.datadict:
            item = self.datadict[f"{key}_selected"]
        if self._mode != InteractionMode.SELECT:
            item = self.datadict[key]
        x = np.array(item.xdata)
        y = np.array(item.ydata)
        F = integrate.cumtrapz(y, x, initial=0)
        self.datadict[key].xdata = item.xdata
        self.datadict[key].ydata = F.tolist()

    add_to_clipboard(self)
    delete_selected_data(self)
    plotting_tools.refresh_plot(self)

def get_inverse_fourier(widget, shortcut, self):
    """
    Perform Inverse Fourier transformation on all selected data
    """
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        if f"{key}_selected" in self.datadict:
            item = self.datadict[f"{key}_selected"]
        if self._mode != InteractionMode.SELECT:
            item = self.datadict[key]
        x = np.array(item.xdata)
        y = np.array(item.ydata)
        y_fourier = np.fft.ifft(y)
        x_fourier = np.fft.fftfreq(len(x), x[1] - x[0])
        y_fourier = [value.real for value in y_fourier]
        x_fourier, y_fourier = sort_data(x_fourier.tolist(), y_fourier)
        self.datadict[key].ydata =  y_fourier
        self.datadict[key].xdata = x_fourier
    add_to_clipboard(self)
    delete_selected_data(self)
    plotting_tools.refresh_plot(self)
    
def combine_data(widget, shortcut, self):
    """
    Combine the selected data into a new data set
    """
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    selected_keys = utilities.get_selected_keys(self)
    
    new_xdata = []
    new_ydata = []
    for key in selected_keys:
        if f"{key}_selected" in self.datadict:
            item = self.datadict[f"{key}_selected"]
        if self._mode != InteractionMode.SELECT:
            item = self.datadict[key]
        new_xdata.extend(item.xdata.copy())
        new_ydata.extend(item.ydata.copy())
    new_xdata, new_ydata = sort_data(new_xdata, new_ydata)
    
    #Create the sample itself
    new_item = utilities.create_data(self, xdata = new_xdata, ydata = new_ydata, name = "Combined Data")
    filename_list = utilities.get_all_filenames(self)
        
    if new_item.filename in filename_list:
         new_item.filename = graphs.get_duplicate_filename(self, new_item.filename)
    new_item.xdata_clipboard = [new_item.xdata.copy()]
    new_item.ydata_clipboard = [new_item.ydata.copy()]
    new_item.clipboard_pos = -1
    color = plotting_tools.get_next_color(self)
    self.datadict[new_item.id] = new_item
    
    delete_selected_data(self)
    add_to_clipboard(self)
    graphs.add_sample_to_menu(self, new_item.filename, color, new_item.id)
    graphs.select_item(self, new_item.id)
    plotting_tools.refresh_plot(self)

def get_fourier(widget, shortcut, self):
    """
    Perform Fourier transformation on all selected data
    """
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        if f"{key}_selected" in self.datadict:
            item = self.datadict[f"{key}_selected"]
        if self._mode != InteractionMode.SELECT:
            item = self.datadict[key]
        x = np.array(item.xdata)
        y = np.array(item.ydata)
        y_fourier = np.fft.fft(y)
        x_fourier = np.fft.fftfreq(len(x), x[1] - x[0])
        y_fourier = [value.real for value in y_fourier]
        x_fourier, y_fourier = sort_data(x_fourier.tolist(), y_fourier)
        self.datadict[key].ydata =  y_fourier
        self.datadict[key].xdata = x_fourier
    delete_selected_data(self)
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def smoothen_data(widget, shortcut, self):
    """
    Smoothen y-data.
    """
    selected_keys = utilities.get_selected_keys(self)
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    for key in selected_keys:
        if f"{key}_selected" in self.datadict:
            #Define the highlighted area
            selected_item = self.datadict[f"{key}_selected"]
            #Perform the operation on the highlighted area
            selected_item.ydata = smooth(selected_item.ydata, 4)
            start_index, stop_index = start_stop[key][0], start_stop[key][1]
            #Replace the highlighted part in the original data set
            self.datadict[key].ydata[start_index:stop_index] = selected_item.ydata
        if self._mode != InteractionMode.SELECT:
            ydata = self.datadict[key].ydata
            ydata = smooth(ydata, 4)
            self.datadict[key].ydata = ydata
    delete_selected_data(self)
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
    selected_keys = utilities.get_selected_keys(self)
    shift_value_log = 1
    shift_value_linear = 0
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
        
    for key in selected_keys:
        if f"{key}_selected" in self.datadict:
            #Define the highlighted area
            selected_item = self.datadict[f"{key}_selected"]
            ymin = min(x for x in selected_item.ydata if x != 0)
            ymax = max(x for x in selected_item.ydata if x != 0)
            shift_value_linear += 1.2*(ymax - ymin)
            shift_value_log *= 10**(np.log10(ymax/ymin))
            shift_item(self, selected_item, shift_value_log, shift_value_linear)
            start_index, stop_index = start_stop[key][0], start_stop[key][1]
            self.datadict[key].ydata[start_index:stop_index] = selected_item.ydata
        if self._mode != InteractionMode.SELECT:
            item = self.datadict[key]
            ymin = min(x for x in item.ydata if x != 0)
            ymax = max(x for x in item.ydata if x != 0)
            shift_value_linear += 1.2*(ymax - ymin)
            shift_value_log *= 10**(np.log10(ymax/ymin))
            shift_item(self, item, shift_value_log, shift_value_linear)

    delete_selected_data(self)
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)

def shift_item(self, item, shift_value_log, shift_value_linear):
    #Check which axes the data is on, so it can choose the appropriate
    #scaling (log/linear)
    if item.plot_Y_position == "left":
        if self.plot_settings.yscale == "log":
            item.ydata = [value * shift_value_log for value in item.ydata]
        if self.plot_settings.yscale == "linear":
            item.ydata = [value + shift_value_linear for value in item.ydata]
    if item.plot_Y_position == "right":
        if self.plot_settings.right_scale == "log":
            item.ydata = [value * shift_value_log for value in item.ydata]
        if self.plot_settings.right_scale == "linear":
            item.ydata = [value + shift_value_linear for value in item.ydata]

def translate_x(shortcut, _, self):
    """
    Translate all selected data on the x-axis
    Amount to be shifted is equal to the value in the translate_x entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    win = self.props.active_window
    try:
        offset = eval(win.translate_x_entry.get_text())
    except Exception as e:
        exception_type = e.__class__.__name__
        print(f"{e}: Unable to do translation, make sure to enter a valid number")
        win.toast_overlay.add_toast(Adw.Toast(title=f"{exception_type}: Unable to do translation, make sure to enter a valid number"))
        offset = 0
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    selected_keys = utilities.get_selected_keys(self)
    for key in selected_keys:
        if f"{key}_selected" in self.datadict:
            #Define the highlighted area
            selected_item = self.datadict[f"{key}_selected"]
            #Perform the operation on the highlighted area
            selected_item.xdata = [value + offset for value in selected_item.xdata]
            start_index, stop_index = start_stop[key][0], start_stop[key][1]
            #Replace the highlighted part in the original data set
            self.datadict[key].xdata[start_index:stop_index] = selected_item.xdata
        if self._mode != InteractionMode.SELECT:
            self.datadict[key].xdata = [value + offset for value in self.datadict[key].xdata]
        self.datadict[key].xdata, self.datadict[key].ydata = sort_data(self.datadict[key].xdata, self.datadict[key].ydata)
    add_to_clipboard(self)
    delete_selected_data(self)
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
        offset = eval(win.translate_y_entry.get_text())
    except Exception as e:
        exception_type = e.__class__.__name__
        print(f"{e}: Unable to do translation, make sure to enter a valid number")
        win.toast_overlay.add_toast(Adw.Toast(title=f"{exception_type}: Unable to do translation, make sure to enter a valid number"))
        offset = 0
    selected_keys = utilities.get_selected_keys(self)

    # If we are in selection mode, then select the highlighted data
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    for key in selected_keys:
        #If the selected data exists, so this will get ignored when we're not in selection mode
        if f"{key}_selected" in self.datadict:
            print(self.datadict[key].filename)
            #Define the highlighted area
            selected_item = self.datadict[f"{key}_selected"]
            #Perform the operation on the highlighted area
            selected_item.ydata = [value + offset for value in selected_item.ydata]
            start_index, stop_index = start_stop[key][0], start_stop[key][1]
            #Replace the highlighted part in the original data set
            self.datadict[key].ydata[start_index:stop_index] = selected_item.ydata
        if self._mode != InteractionMode.SELECT:
            self.datadict[key].ydata = [value + offset for value in self.datadict[key].ydata]
    add_to_clipboard(self)
    #Throw away the selected/highlighted datasets
    delete_selected_data(self)
    plotting_tools.refresh_plot(self)

def multiply_x(shortcut, _, self):
    """
    Multiply all selected data on the x-axis
    Amount to be shifted is equal to the value in the multiply_x entry widget
    Will show a toast if a ValueError is raised, typically when a user entered
    an invalid number (e.g. comma instead of point separators)
    """
    win = self.props.active_window
    try:
        multiplier = eval(win.multiply_x_entry.get_text())
    except Exception as e:
        exception_type = e.__class__.__name__
        print(f"{e}: Unable to do multiplication, make sure to enter a valid number")
        win.toast_overlay.add_toast(Adw.Toast(title=f"{exception_type}: Unable to do multiplication, make sure to enter a valid number"))
        multiplier = 1
    selected_keys = utilities.get_selected_keys(self)
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    for key in selected_keys:
        #If the selected data exists, so this will get ignored when we're not in selection mode
        if f"{key}_selected" in self.datadict:
            #Define the highlighted area
            selected_item = self.datadict[f"{key}_selected"]
            #Perform the operation on the highlighted area
            selected_item.xdata = [value * multiplier for value in selected_item.xdata]
            start_index, stop_index = start_stop[key][0], start_stop[key][1]
            #Replace the highlighted part in the original data set
            self.datadict[key].xdata[start_index:stop_index] = selected_item.xdata
        if self._mode != InteractionMode.SELECT:
            self.datadict[key].xdata = [value * multiplier for value in self.datadict[key].xdata]
        self.datadict[key].xdata, self.datadict[key].ydata = sort_data(self.datadict[key].xdata, self.datadict[key].ydata)
    delete_selected_data(self)
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
        multiplier = eval(win.multiply_y_entry.get_text())
    except Exception as e:
        exception_type = e.__class__.__name__
        print(f"{e}: Unable to do multiplication, make sure to enter a valid number")
        win.toast_overlay.add_toast(Adw.Toast(title=f"{exception_type}: Unable to do multiplication, make sure to enter a valid number"))
        multiplier = 1
    selected_keys = utilities.get_selected_keys(self)
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    for key in selected_keys:
        #If the selected data exists, so this will get ignored when we're not in selection mode
        if f"{key}_selected" in self.datadict:
            #Define the highlighted area
            selected_item = self.datadict[f"{key}_selected"]
            #Perform the operation on the highlighted area
            selected_item.ydata = [value * multiplier for value in selected_item.ydata]
            start_index, stop_index = start_stop[key][0], start_stop[key][1]
            #Replace the highlighted part in the original data set
            self.datadict[key].ydata[start_index:stop_index] = selected_item.ydata
        if self._mode != InteractionMode.SELECT:
            self.datadict[key].ydata = [value * multiplier for value in self.datadict[key].ydata]
    delete_selected_data(self)
    add_to_clipboard(self)
    plotting_tools.refresh_plot(self)


def normalize_data(shortcut, _, self):
    """
    Normalize all selected data
    """
    selected_keys = utilities.get_selected_keys(self)
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    for key in selected_keys:
        #If the selected data exists, so this will get ignored when we're not in selection mode
        if f"{key}_selected" in self.datadict:
            #Define the highlighted area
            selected_item = self.datadict[f"{key}_selected"]
            #Perform the operation on the highlighted area
            selected_item.ydata = normalize(selected_item.ydata)
            start_index, stop_index = start_stop[key][0], start_stop[key][1]
            #Replace the highlighted part in the original data set
            self.datadict[key].ydata[start_index:stop_index] = selected_item.ydata
            self.datadict[key].xdata[start_index:stop_index] = selected_item.xdata
        if self._mode != InteractionMode.SELECT:
            self.datadict[key].ydata = normalize(self.datadict[key].ydata)
    delete_selected_data(self)
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
    if self._mode == InteractionMode.SELECT:
        selection, start_stop = select_data(self)
    for key in selected_keys:
        #If the selected data exists, so this will get ignored when we're not in selection mode
        if f"{key}_selected" in self.datadict:
            #Define the highlighted area
            selected_item = self.datadict[f"{key}_selected"]
            #Perform the operation on the highlighted area
            if self.preferences.config["action_center_data"] == "Center at maximum Y value":
                selected_item.xdata = center_data_max_Y(selected_item.xdata, selected_item.ydata)
            elif self.preferences.config["action_center_data"] == "Center at middle coordinate":
                selected_item.xdata = center_data_middle(selected_item.xdata)
            start_index, stop_index = start_stop[key][0], start_stop[key][1]
            #Replace the highlighted part in the original data set
            self.datadict[key].ydata[start_index:stop_index] = selected_item.ydata
            self.datadict[key].xdata[start_index:stop_index] = selected_item.xdata
            self.datadict[key].xdata, self.datadict[key].ydata = sort_data(self.datadict[key].xdata, self.datadict[key].ydata)
        if self._mode != InteractionMode.SELECT:
            if self.preferences.config["action_center_data"] == "Center at maximum Y value":
                self.datadict[key].xdata = center_data_max_Y(self.datadict[key].xdata, self.datadict[key].ydata)
            elif self.preferences.config["action_center_data"] == "Center at middle coordinate":
                self.datadict[key].xdata = center_data_middle(self.datadict[key].xdata)
            self.datadict[key].xdata, self.datadict[key].ydata = sort_data(self.datadict[key].xdata, self.datadict[key].ydata)
    delete_selected_data(self)
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
