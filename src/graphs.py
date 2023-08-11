# SPDX-License-Identifier: GPL-3.0-or-later
from gettext import gettext as _

from graphs import file_io, plot_styles, plotting_tools, ui, utilities
from graphs.canvas import Canvas

from matplotlib import pyplot


def add_items(self, items):
    if not items:
        return
    ignored = []
    handle_duplicates = \
        self.settings.get_child("general").get_enum("handle-duplicates")
    for item in items:
        for item_1 in self.datadict.values():
            if item.name == item_1.name:
                if handle_duplicates == 0:  # Auto-add
                    i = 0
                    while True:
                        i += 1
                        if f"{item.name} ({i})" not in \
                                utilities.get_all_names(self):
                            new_name = f"{item.name} ({i})"
                            break
                    item.name = new_name
                elif handle_duplicates == 1:  # Ignore
                    ignored.append(item.name)
                    continue
                elif handle_duplicates == 3:  # Override
                    item.key = item_1.key
        if item.xlabel:
            original_position = item.xposition
            if item.xposition == "bottom":
                if self.plot_settings.bottom_label == "":
                    self.plot_settings.bottom_label = item.xlabel
                elif item.xlabel != self.plot_settings.bottom_label:
                    item.xposition = "top"
            if item.xposition == "top":
                if self.plot_settings.top_label == "":
                    self.plot_settings.top_label = item.xlabel
                elif item.xlabel != self.plot_settings.bottom_label:
                    item.xposition = original_position
        if item.ylabel:
            original_position = item.yposition
            if item.yposition == "left":
                if self.plot_settings.left_label == "":
                    self.plot_settings.left_label = item.ylabel
                elif item.ylabel != self.plot_settings.left_label:
                    item.yposition = "right"
            if item.yposition == "right":
                if self.plot_settings.right_label == "":
                    self.plot_settings.right_label = item.ylabel
                elif item.ylabel != self.plot_settings.left_label:
                    item.yposition = original_position
        if item.color == "":
            item.color = plotting_tools.get_next_color(self)
        self.datadict[item.key] = item

    if ignored:
        if len(ignored) > 1:
            toast = _("Items {} already exist").format(", ".join(ignored))
        else:
            toast = _("Item {} already exists")
        self.main_window.add_toast(toast)
    self.main_window.item_list.set_visible(True)
    ui.reload_item_menu(self)
    ui.enable_data_dependent_buttons(self)
    refresh(self)
    plotting_tools.optimize_limits(self)
    self.props.clipboard.add()


def delete_item(self, key, give_toast=False):
    name = self.datadict[key].name
    del self.datadict[key]
    ui.reload_item_menu(self)
    if give_toast:
        self.main_window.add_toast(_("Deleted {name}").format(name=name))
    self.props.clipboard.add()


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
    self.canvas.set_ticks()
    hide_unselected = \
        self.settings.get_child("general").get_boolean("hide-unselected")
    for item in reversed(self.datadict.values()):
        if item is None or (hide_unselected and not item.selected):
            continue
        self.canvas.plot(item)
    self.canvas.set_legend()
    self.canvas.draw()
