# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw

from graphs import file_io, plotting_tools, samplerow, ui, utilities
from graphs.canvas import Canvas
from graphs.data import Data
from graphs.misc import DummyToolbar, ImportMode, ImportSettings


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
            color = self.item_rows[key].color_picker.color
            y_axis = item.plot_Y_position
            x_axis = item.plot_X_position
            plotting_tools.plot_figure(self, self.canvas, item.xdata, item.ydata, item.filename, linewidth, linestyle, color, marker, marker_size, y_axis, x_axis)


def open_files(self, files, import_settings):
    if import_settings is None:
        import_settings = ImportSettings(self)
    if len(files) > 1:
        import_settings.mode = ImportMode.MULTIPLE
    elif len(files) == 1:
        import_settings.mode = ImportMode.SINGLE
    for file in files:
        path = file.peek_path()
        if path != '':
            try:
                import_settings.path = path
                item = file_io.get_data(self, import_settings)
                if item.xdata == []:
                    self.main_window.toast_overlay.add_toast(Adw.Toast(title='At least one data set could not be imported'))
                    continue
            except IndexError:
                self.main_window.toast_overlay.add_toast(Adw.Toast(title='Could not open data, the column index was out of range'))
                break
            except UnicodeDecodeError:
                self.main_window.toast_overlay.add_toast(Adw.Toast(title='Could not open data, wrong filetype'))
                break
            if item is not None:
                handle_duplicates = self.preferences.config['handle_duplicates']
                if not handle_duplicates == 'Add duplicates':
                    for key, item2 in self.datadict.items():
                        if item.filename == item2.filename:
                            if handle_duplicates == 'Auto-rename duplicates':
                                item.filename = utilities.get_duplicate_filename(self, item.filename)
                            elif handle_duplicates == 'Ignore duplicates':
                                self.main_window.toast_overlay.add_toast(Adw.Toast(title=f'Item \'{item.filename}\' already exists'))
                                return
                            elif handle_duplicates == 'Override existing items':
                                y_axis = item.plot_Y_position
                                x_axis = item.plot_X_position
                                self.datadict[key] = item
                                plotting_tools.reload_plot(self)
                                return
                y_axis = item.plot_Y_position
                x_axis = item.plot_X_position
                self.datadict[item.key] = item
                item.color = plotting_tools.get_next_color(self)
                plotting_tools.plot_figure(self, self.canvas, item.xdata, item.ydata, item.filename, item.color, y_axis, x_axis)
                add_sample_to_menu(self, item.filename, item.color, item.key, select_item=True)
    self.canvas.draw()
    plotting_tools.set_canvas_limits_axis(self, self.canvas)
    plotting_tools.refresh_plot(self)
    ui.enable_data_dependent_buttons(self, True)


def select_item(self, key):
    item = self.item_rows[key]
    item.check_button.set_active(True)
    plotting_tools.refresh_plot(self)
    ui.enable_data_dependent_buttons(self, utilities.get_selected_keys(self))


def delete(self, key, give_toast=False):
    layout = self.list_box
    for sample_menu_key, item in self.sample_menu.items():
        if sample_menu_key == key:
            layout.remove(item)
    filename = self.datadict[key].filename
    del self.item_rows[key]
    del self.datadict[key]
    if give_toast:
        self.main_window.toast_overlay.add_toast(Adw.Toast(title=f'Deleted {filename}'))

    if len(self.datadict) == 0:
        self.canvas.ax.legend().remove()
        self.canvas.ax.set_prop_cycle(None)
        layout.set_visible(False)
        self.main_window.no_data_label_box.set_visible(True)

    reset_clipboard(self)
    plotting_tools.refresh_plot(self)
    ui.enable_data_dependent_buttons(self, utilities.get_selected_keys(self))


def add_sample_to_menu(self, filename, color, key, select_item=False):
    win = self.main_window
    win.list_box.set_visible(True)
    win.no_data_label_box.set_visible(False)
    self.list_box = win.list_box
    row = samplerow.SampleBox(self, key, color, filename, select_item)
    self.item_rows[key] = row
    self.list_box.append(row)
    self.sample_menu[key] = self.list_box.get_last_child()
    plotting_tools.refresh_plot(self)
    ui.enable_data_dependent_buttons(self, True)


def create_data_from_project(self, new_dictionary):
    """
    Creates self.datadict using a new dictionary.
    This function uses new dictionary, which contains old Data objects in order to
    create a new self.datadict dictionary, with new Data objects.
    It sets all matching attributes that exist in the old data set to the new data set.
    Attributes that were removed and no longer used are not copied over, and will therefore
    revert to the default value.
    """
    self.datadict = {}
    for key, item in new_dictionary.items():
        xdata = item.xdata
        ydata = item.ydata
        self.datadict[item.key] = Data(self, xdata, ydata)
        for attribute in self.datadict[item.key].__dict__:
            if hasattr(item, attribute):
                setattr(self.datadict[item.key], attribute, getattr(item, attribute))


def set_attributes(new_object, template):
    """
    Sets the attributes of `new_object` to match those of `template`.
    This function sets the attributes of `new_object` to the values of the attributes in `template` if they don't already exist in `new_object`.
    Additionally, it removes any attributes from `new_object` that are not present in `template`.
    """
    for attribute in template.__dict__:
        if not hasattr(new_object, attribute):
            setattr(new_object, attribute, getattr(template, attribute))
    for attribute in new_object.__dict__:
        if not hasattr(template, attribute):
            delattr(new_object, attribute)


def load_empty(self):
    win = self.main_window
    xlabel = self.plot_settings.xlabel
    ylabel = self.plot_settings.ylabel
    self.canvas = Canvas(parent=self, xlabel=xlabel, ylabel=ylabel)
    for axis in [self.canvas.right_axis, self.canvas.top_left_axis, self.canvas.top_right_axis]:
        axis.get_xaxis().set_visible(False)
        axis.get_yaxis().set_visible(False)
    self.dummy_toolbar = DummyToolbar(self.canvas)
    win.toast_overlay.set_child(self.canvas)


def reset_clipboard(self):
    for key, item in self.datadict.items():
        item.xdata_clipboard = [item.xdata]
        item.ydata_clipboard = [item.ydata]
        item.clipboard_pos = -1
    ui.disable_clipboard_buttons(self)
