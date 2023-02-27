# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from gi.repository import Adw

from graphs import file_io, plotting_tools, samplerow, ui, utilities
from graphs.data import Data
from graphs.misc import ImportMode, ImportSettings


def open_selection_from_dict(self):
    for key, item in self.datadict.items():
        if item is not None:
            if self.item_rows[key].check_button.get_active():
                linewidth = item.selected_line_thickness
                linestyle = item.linestyle_selected
                marker = item.selected_markers
                marker_size = item.selected_marker_size
            else:
                linewidth = item.unselected_line_thickness
                linestyle = item.linestyle_unselected
                marker = item.unselected_markers
                marker_size = item.unselected_marker_size
            plotting_tools.plot_figure(
                self, self.canvas, item.xdata, item.ydata, item.filename,
                linewidth=linewidth, linestyle=linestyle, color=item.color,
                marker=marker, marker_size=marker_size,
                y_axis=item.plot_y_position, x_axis=item.plot_x_position)


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
                    toast = "At least one data set could not be imported"
                    self.main_window.add_toast(toast)
                    continue
                item = Data(self, xdata, ydata, import_settings)
            except IndexError:
                toast = "Could not open data, the column index is out of range"
                self.main_window.add_toast(toast)
                break
            except UnicodeDecodeError:
                toast = "Could not open data, wrong filetype"
                self.main_window.add_toast(toast)
                break
            if item is not None:
                item.color = plotting_tools.get_next_color(self)
                add_item(self, item)
    plotting_tools.set_canvas_limits_axis(self)


def open_project(self, file):
    for key in self.datadict.copy():
        delete(self, key)
    try:
        new_plot_settings, new_datadict, version = \
            file_io.load_project(file.peek_path())
        if Adw.StyleManager.get_default().get_dark():
            style = self.preferences.config["plot_style_dark"]
        else:
            style = self.preferences.config["plot_style_light"]
        new_plot_settings.plot_style = style
        self.plot_settings = new_plot_settings
        set_attributes(new_plot_settings, self.plot_settings)
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
    win = self.main_window
    handle_duplicates = self.preferences.config["handle_duplicates"]
    for key_1, item_1 in self.datadict.items():
        if item.filename == item_1.filename:
            if handle_duplicates == "Auto-rename duplicates":
                loop = True
                i = 0
                while loop:
                    i += 1
                    new_name = f"{item.filename} ({i})"
                    loop = False
                    for key_2, item_2 in self.datadict.items():
                        if new_name == item_2.filename:
                            loop = True
                item.filename = new_name
            elif handle_duplicates == "Ignore duplicates":
                toast = f'Item "{item.filename}" already exists'
                win.add_toast(toast)
                return
            elif handle_duplicates == "Override existing items":
                self.datadict[key] = item
                plotting_tools.reload_plot(self)
                return
    self.datadict[key] = item
    win.list_box.set_visible(True)
    win.no_data_label_box.set_visible(False)
    row = samplerow.SampleBox(self, key, item.color, item.filename, select)
    self.item_rows[key] = row
    win.list_box.append(row)
    self.sample_menu[key] = win.list_box.get_last_child()
    ui.enable_data_dependent_buttons(self, True)
    plotting_tools.refresh_plot(self)


def select_item(self, key):
    item = self.item_rows[key]
    item.check_button.set_active(True)
    plotting_tools.refresh_plot(self)
    ui.enable_data_dependent_buttons(self, utilities.get_selected_keys(self))


def delete(self, key, give_toast=False):
    layout = self.main_window.list_box
    for sample_menu_key, item in self.sample_menu.items():
        if sample_menu_key == key:
            layout.remove(item)
    filename = self.datadict[key].filename
    del self.item_rows[key]
    del self.datadict[key]
    if give_toast:
        self.main_window.add_toast(f"Deleted {filename}")

    if len(self.datadict) == 0:
        self.canvas.ax.legend().remove()
        self.canvas.ax.set_prop_cycle(None)
        layout.set_visible(False)
        self.main_window.no_data_label_box.set_visible(True)

    reset_clipboard(self)
    plotting_tools.refresh_plot(self)
    ui.enable_data_dependent_buttons(self, utilities.get_selected_keys(self))


def set_attributes(new_object, template):
    """
    Sets the attributes of `new_object` to match those of `template`.
    This function sets the attributes of `new_object` to the values of the
    attributes in `template` if they don"t already exist in `new_object`.
    Additionally, it removes any attributes from `new_object` that are
    not present in `template`.
    """
    for attribute in template.__dict__:
        if not hasattr(new_object, attribute):
            setattr(new_object, attribute, getattr(template, attribute))
    for attribute in new_object.__dict__:
        if not hasattr(template, attribute):
            delattr(new_object, attribute)


def reset_clipboard(self):
    for _key, item in self.datadict.items():
        item.xdata_clipboard = [item.xdata]
        item.ydata_clipboard = [item.ydata]
        item.clipboard_pos = -1
    ui.disable_clipboard_buttons(self)
