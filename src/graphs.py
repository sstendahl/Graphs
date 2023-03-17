# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from gi.repository import Adw

from graphs import clipboard, file_io, plotting_tools, samplerow, ui, utilities
from graphs.canvas import Canvas
from graphs.data import Data
from graphs.misc import ImportMode, ImportSettings


def open_files(self, files, import_settings):
    if import_settings is None:
        import_settings = ImportSettings(self)
    if len(files) > 1:
        import_settings.mode = ImportMode.MULTIPLE
    elif len(files) == 1:
        import_settings.mode = ImportMode.SINGLE
    for file in files:
        path = file.peek_path()
        if path != "":
            try:
                import_settings.path = path
                xdata, ydata = file_io.get_data(self, import_settings)
                if xdata == []:
                    filename = import_settings.path.split("/")[-1]
                    toast = f"Unable to retreive data for {filename}"
                    self.main_window.add_toast(toast)
                    continue
                item = Data(self, xdata, ydata, import_settings)
                item.color = plotting_tools.get_next_color(self)
                add_item(self, item)
            except IndexError:
                toast = "Could not open data, the column index is out of range"
                self.main_window.add_toast(toast)
                continue
            except UnicodeDecodeError:
                toast = "Could not open data, wrong filetype"
                self.main_window.add_toast(toast)
                continue
    self.canvas.set_limits()


def open_project(self, file):
    for key in self.datadict.copy():
        delete_item(self, key)
    try:
        new_plot_settings, new_datadict, _version = \
            file_io.load_project(file.peek_path())
        if Adw.StyleManager.get_default().get_dark():
            style = self.preferences.config["plot_style_dark"]
        else:
            style = self.preferences.config["plot_style_light"]
        new_plot_settings.plot_style = style
        self.plot_settings = new_plot_settings
        utilities.set_attributes(new_plot_settings, self.plot_settings)
        self.datadict = {}
        for key, item in new_datadict.items():
            new_item = Data(self, item.xdata, item.ydata)
            for attribute in new_item.__dict__:
                if hasattr(item, attribute):
                    setattr(new_item, attribute, getattr(item, attribute))
            add_item(self, new_item)
        ui.enable_data_dependent_buttons(
            self, utilities.get_selected_keys(self))
    except Exception:
        message = "Could not open project"
        self.main_window.add_toast(message)
        logging.exception(message)


def add_item(self, item, select=True):
    key = item.key
    handle_duplicates = self.preferences.config["handle_duplicates"]
    for _key_1, item_1 in self.datadict.items():
        if item.filename == item_1.filename:
            if handle_duplicates == "Auto-rename duplicates":
                loop = True
                i = 0
                while loop:
                    i += 1
                    new_name = f"{item.filename} ({i})"
                    loop = False
                    for _key_2, item_2 in self.datadict.items():
                        if new_name == item_2.filename:
                            loop = True
                item.filename = new_name
            elif handle_duplicates == "Ignore duplicates":
                toast = f'Item "{item.filename}" already exists'
                self.main_window.add_toast(toast)
                return
            elif handle_duplicates == "Override existing items":
                self.datadict[key] = item
                reload(self)
                return
    self.datadict[key] = item
    self.main_window.list_box.set_visible(True)
    self.main_window.no_data_label_box.set_visible(False)
    row = samplerow.SampleBox(self, key, item.color, item.filename, select)
    self.item_rows[key] = row
    self.main_window.list_box.append(row)
    self.sample_menu[key] = self.main_window.list_box.get_last_child()
    clipboard.reset(self)
    reload(self)
    ui.enable_data_dependent_buttons(self, True)


def select_item(self, key):
    self.item_rows[key].check_button.set_active(True)
    refresh(self)
    ui.enable_data_dependent_buttons(self, utilities.get_selected_keys(self))


def delete_item(self, key, give_toast=False):
    for sample_menu_key, item in self.sample_menu.items():
        if sample_menu_key == key:
            self.main_window.list_box.remove(item)
    filename = self.datadict[key].filename
    del self.item_rows[key]
    del self.datadict[key]
    if give_toast:
        self.main_window.add_toast(f"Deleted {filename}")
    clipboard.reset(self)
    if self.datadict:
        refresh(self)
        ui.enable_data_dependent_buttons(
            self, utilities.get_selected_keys(self))
    else:
        reload(self)
        self.main_window.no_data_label_box.set_visible(True)
        self.main_window.list_box.set_visible(False)
        ui.enable_data_dependent_buttons(self, False)


def reload(self):
    """Completely reload the plot of the graph"""
    self.canvas = Canvas(parent=self)
    self.main_window.toast_overlay.set_child(self.canvas)
    refresh(self)
    self.set_mode(None, None, self.interaction_mode)
    self.canvas.grab_focus()


def refresh(self, set_limits=False):
    """Refresh the graph without completely reloading it."""
    canvas = self.canvas
    for line in canvas.ax.lines + canvas.right_axis.lines + \
            canvas.top_left_axis.lines + canvas.top_right_axis.lines:
        line.remove()
    if len(self.datadict) > 0:
        plotting_tools.hide_unused_axes(self, canvas)
    for key, item in self.datadict.items():
        if item is not None:
            selected = self.item_rows[key].check_button.get_active()
            self.canvas.plot(item, selected)
    if set_limits and len(self.datadict) > 0:
        self.canvas.set_limits()
    self.canvas.draw()
