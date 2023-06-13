# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _
from pickle import UnpicklingError

from graphs import (clipboard, file_io, plot_styles, plotting_tools, ui,
                    utilities)
from graphs.canvas import Canvas
from graphs.item import Item

from matplotlib import pyplot


def open_project(self, file):
    for key in self.datadict.copy():
        delete_item(self, key)
    try:
        new_plot_settings, new_datadict, datadict_clipboard, clipboard_pos, \
            _version = file_io.read_project(file)
        utilities.set_attributes(new_plot_settings, self.plot_settings)
        self.plot_settings = new_plot_settings
        self.datadict = {}
        add_items(self,
                  [utilities.check_item(self, item)
                   for item in new_datadict.values()])
        self.clipboard_pos = clipboard_pos
        self.datadict_clipboard = datadict_clipboard
    except (EOFError, UnpicklingError):
        message = _("Could not open project")
        self.main_window.add_toast(message)
        logging.exception(message)


def add_items(self, items):
    if not items:
        return
    ignored = []
    handle_duplicates = self.preferences["handle_duplicates"]
    for item in items:
        for item_1 in self.datadict.values():
            if item.name == item_1.name:
                if handle_duplicates == "Auto-rename duplicates":
                    i = 0
                    while True:
                        i += 1
                        if f"{item.name} ({i})" not in \
                                utilities.get_all_names(self):
                            new_name = f"{item.name} ({i})"
                            break
                    item.name = new_name
                elif handle_duplicates == "Ignore duplicates":
                    ignored.append(item.name)
                    continue
                elif handle_duplicates == "Override existing items":
                    item.key = item_1.key
        if item.xlabel:
            original_position = item.plot_x_position
            if item.plot_x_position == "bottom":
                if self.plot_settings.xlabel \
                        == self.preferences["plot_x_label"]:
                    self.plot_settings.xlabel = item.xlabel
                elif item.xlabel != self.plot_settings.xlabel:
                    item.plot_x_position = "top"
            if item.plot_x_position == "top":
                if self.plot_settings.top_label \
                        == self.preferences["plot_top_label"]:
                    self.plot_settings.top_label = item.xlabel
                elif item.xlabel != self.plot_settings.xlabel:
                    item.plot_x_position = original_position
        if item.ylabel:
            original_position = item.plot_y_position
            if item.plot_y_position == "left":
                if self.plot_settings.ylabel \
                        == self.preferences["plot_y_label"]:
                    self.plot_settings.ylabel = item.ylabel
                elif item.ylabel != self.plot_settings.ylabel:
                    item.plot_y_position = "right"
            if item.plot_y_position == "right":
                if self.plot_settings.right_label \
                        == self.preferences["plot_right_label"]:
                    self.plot_settings.right_label = item.ylabel
                elif item.ylabel != self.plot_settings.ylabel:
                    item.plot_y_position = original_position
        if item.color is None and isinstance(item, Item):
            item.color = plotting_tools.get_next_color(self)
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
    ui.enable_data_dependent_buttons(self)
    refresh(self)
    plotting_tools.optimize_limits(self)


def delete_item(self, key, give_toast=False):
    name = self.datadict[key].name
    del self.datadict[key]
    ui.reload_item_menu(self)
    if give_toast:
        self.main_window.add_toast(_("Deleted {name}").format(name=name))
    clipboard.add(self)
    check_open_data(self)


def check_open_data(self):
    self.main_window.item_list.set_visible(self.datadict)
    refresh(self)
    ui.enable_data_dependent_buttons(self)


def reload(self):
    """Completely reload the plot of the graph"""
    pyplot.rcParams.update(
        file_io.parse_style(plot_styles.get_preferred_style(self)))
    self.canvas = Canvas(self)
    self.main_window.toast_overlay.set_child(self.canvas)
    refresh(self)
    self.set_mode(None, None, self.interaction_mode)
    self.canvas.grab_focus()


def refresh(self):
    """Refresh the graph without completely reloading it."""
    remove = []
    for axis in [self.canvas.axis, self.canvas.right_axis,
                 self.canvas.top_left_axis, self.canvas.top_right_axis]:
        remove.extend(axis.lines + axis.texts)
    for item in remove:
        item.remove()
    if len(self.datadict) > 0:
        plotting_tools.hide_unused_axes(self, self.canvas)
    self.canvas.set_axis_properties()
    for item in reversed(self.datadict.values()):
        if (item is not None) and not \
                (self.preferences["hide_unselected"] and not item.selected):
            self.canvas.plot(item)
    self.canvas.set_legend()
    self.canvas.draw()
