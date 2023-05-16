# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _
from pickle import UnpicklingError

from graphs import clipboard, file_io, plotting_tools, ui, utilities
from graphs.canvas import Canvas
from graphs.item import Item


def open_project(self, file):
    for key in self.datadict.copy():
        delete_item(self, key)
    try:
        new_plot_settings, new_datadict, datadict_clipboard, clipboard_pos, \
            _version = file_io.read_project(file)
        utilities.set_attributes(new_plot_settings, self.plot_settings)
        self.plot_settings = new_plot_settings
        self.clipboard_pos = clipboard_pos
        self.datadict_clipboard = datadict_clipboard
        self.datadict = {}
        items = []
        for item in new_datadict.values():
            new_item = Item(self, item.xdata, item.ydata)
            for attribute in new_item.__dict__:
                if hasattr(item, attribute):
                    setattr(new_item, attribute, getattr(item, attribute))
            items.append(new_item)
        add_items(self, items)
        self.datadict_clipboard = self.datadict_clipboard[:-1]
    except (EOFError, UnpicklingError):
        message = _("Could not open project")
        self.main_window.add_toast(message)
        logging.exception(message)


def add_items(self, items):
    if not items:
        return
    ignored = []
    for item in items:
        handle_duplicates = self.preferences.config["handle_duplicates"]
        for item_1 in self.datadict.values():
            if item.name == item_1.name:
                if handle_duplicates == "Auto-rename duplicates":
                    loop = True
                    i = 0
                    while loop:
                        i += 1
                        new_name = f"{item.name} ({i})"
                        loop = False
                        for item_2 in self.datadict.values():
                            if new_name == item_2.name:
                                loop = True
                    item.name = new_name
                elif handle_duplicates == "Ignore duplicates":
                    ignored.append(item.name)
                    continue
                elif handle_duplicates == "Override existing items":
                    self.datadict[item.key] = item
                    continue
        self.datadict[item.key] = item
    if ignored:
        if len(ignored) > 1:
            toast = _("Items {} already exist").format(", ".join(ignored))
        else:
            toast = _("Item {} already exists")
        self.main_window.add_toast(toast)
    clipboard.add(self)
    self.main_window.item_list.set_visible(True)
    ui.reload_item_menu(self)
    ui.enable_data_dependent_buttons(self, True)
    reload(self)


def delete_item(self, key, give_toast=False):
    name = self.datadict[key].name
    del self.datadict[key]
    ui.reload_item_menu(self)
    if give_toast:
        self.main_window.add_toast(_("Deleted {name}").format(name=name))
    clipboard.add(self)
    check_open_data(self)


def check_open_data(self):
    if self.datadict:
        self.main_window.item_list.set_visible(True)
        refresh(self, set_limits=True)
        ui.enable_data_dependent_buttons(
            self, utilities.get_selected_keys(self))
    else:
        reload(self)
        self.main_window.item_list.set_visible(False)
        ui.enable_data_dependent_buttons(self, False)


def reload(self, reset_limits=True):
    """Completely reload the plot of the graph"""
    limits = self.canvas.get_limits()
    self.canvas = Canvas(parent=self)
    self.main_window.toast_overlay.set_child(self.canvas)
    refresh(self, set_limits=reset_limits)
    if not reset_limits:
        self.canvas.set_limits(limits)
    self.set_mode(None, None, self.interaction_mode)
    self.canvas.grab_focus()


def refresh(self, set_limits=False):
    """Refresh the graph without completely reloading it."""
    for line in self.canvas.axis.lines + self.canvas.right_axis.lines + \
            self.canvas.top_left_axis.lines + self.canvas.top_right_axis.lines:
        line.remove()
    if len(self.datadict) > 0:
        plotting_tools.hide_unused_axes(self, self.canvas)
    for item in reversed(self.datadict.values()):
        if (item is not None) and not \
                (self.preferences.config["hide_unselected"] and not
                 item.selected):
            self.canvas.plot(item)
    if set_limits and len(self.datadict) > 0:
        self.canvas.restore_view()
    self.canvas.draw()
