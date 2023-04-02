# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from pathlib import Path

from graphs import clipboard, file_io, plotting_tools, ui, utilities
from graphs.canvas import Canvas
from graphs.item import Item
from graphs.misc import ImportMode, ImportSettings
from graphs.item_box import ItemBox


def open_files(self, files, import_settings):
    if import_settings is None:
        import_settings = ImportSettings(self.preferences.config)
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
                    filename = Path(import_settings.path).name
                    toast = f"Unable to retreive data for {filename}"
                    self.main_window.add_toast(toast)
                    continue
                name = import_settings.name
                if name == "":
                    name = Path(import_settings.path).name
                color = plotting_tools.get_next_color(self)
                cfg = self.preferences.config
                add_item(self, Item(cfg, xdata, ydata, name, color))
            except IndexError:
                toast = "Could not open data, the column index is out of range"
                self.main_window.add_toast(toast)
                continue
            except UnicodeDecodeError:
                toast = "Could not open data, wrong filetype"
                self.main_window.add_toast(toast)
                continue
    self.canvas.set_limits()


def open_project(self, path):
    for key in self.datadict.copy():
        delete_item(self, key)
    try:
        new_plot_settings, new_datadict, _version = \
            file_io.load_project(path)
        self.plot_settings = new_plot_settings
        utilities.set_attributes(new_plot_settings, self.plot_settings)
        self.datadict = {}
        for key, item in new_datadict.items():
            new_item = Item(self.preferences.config, item.xdata, item.ydata)
            for attribute in new_item.__dict__:
                if hasattr(item, attribute):
                    setattr(new_item, attribute, getattr(item, attribute))
            add_item(self, new_item, reset_clipboard=False)
        if len(item.xdata_clipboard) > 1:
            undo_button = self.main_window.undo_button
            undo_button.set_sensitive(True)
        ui.enable_data_dependent_buttons(
            self, utilities.get_selected_keys(self))
        self.canvas.set_limits()
    except Exception:
        message = "Could not open project"
        self.main_window.add_toast(message)
        logging.exception(message)


def add_item(self, item, reset_clipboard=True):
    key = item.key
    handle_duplicates = self.preferences.config["handle_duplicates"]
    for _key_1, item_1 in self.datadict.items():
        if item.name == item_1.name:
            if handle_duplicates == "Auto-rename duplicates":
                loop = True
                i = 0
                while loop:
                    i += 1
                    new_name = f"{item.name} ({i})"
                    loop = False
                    for _key_2, item_2 in self.datadict.items():
                        if new_name == item_2.name:
                            loop = True
                item.name = new_name
            elif handle_duplicates == "Ignore duplicates":
                toast = f'Item "{item.name}" already exists'
                self.main_window.add_toast(toast)
                return
            elif handle_duplicates == "Override existing items":
                self.datadict[key] = item
                reload(self)
                return
    self.datadict[key] = item
    self.main_window.list_box.set_visible(True)
    self.main_window.no_data_label_box.set_visible(False)
    self.item_boxes[key] = ItemBox(self, item)
    self.main_window.list_box.append(self.item_boxes[key])
    self.item_menu[key] = self.main_window.list_box.get_last_child()
    if reset_clipboard:
        clipboard.reset(self)
    reload(self)
    ui.enable_data_dependent_buttons(self, True)


def delete_item(self, key, give_toast=False):
    self.main_window.list_box.remove(self.item_menu[key])
    name = self.datadict[key].name
    del self.item_boxes[key]
    del self.datadict[key]
    if give_toast:
        self.main_window.add_toast(f"Deleted {name}")
    clipboard.reset(self)
    if self.datadict:
        refresh(self, set_limits=True)
        ui.enable_data_dependent_buttons(
            self, utilities.get_selected_keys(self))
    else:
        reload(self, set_limits=True)
        self.main_window.no_data_label_box.set_visible(True)
        self.main_window.list_box.set_visible(False)
        ui.enable_data_dependent_buttons(self, False)


def reload(self):
    """Completely reload the plot of the graph"""
    self.canvas = Canvas(parent=self)
    self.main_window.toast_overlay.set_child(self.canvas)
    refresh(self, set_limits=True)
    self.set_mode(None, None, self.interaction_mode)
    self.canvas.grab_focus()


def refresh(self, set_limits=False):
    """Refresh the graph without completely reloading it."""
    canvas = self.canvas
    for line in canvas.axis.lines + canvas.right_axis.lines + \
            canvas.top_left_axis.lines + canvas.top_right_axis.lines:
        line.remove()
    if len(self.datadict) > 0:
        plotting_tools.hide_unused_axes(self, canvas)
    for _key, item in self.datadict.items():
        if item is not None:
            self.canvas.plot(item, item.selected)
    if set_limits and len(self.datadict) > 0:
        self.canvas.set_limits()
    self.canvas.draw()
