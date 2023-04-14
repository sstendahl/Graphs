# SPDX-License-Identifier: GPL-3.0-or-later
import os

from gi.repository import Adw, GLib, Gtk

from graphs import file_io, graphs, utilities
from graphs.item_box import ItemBox


def on_style_change(_shortcut, _theme, _widget, self):
    graphs.reload(self)


def enable_data_dependent_buttons(self, enabled):
    win = self.main_window
    dependent_buttons = [
        win.shift_vertically_button,
        win.translate_x_button,
        win.translate_y_button,
        win.multiply_x_button,
        win.multiply_y_button,
        win.smooth_button,
        win.fourier_button,
        win.inverse_fourier_button,
        win.normalize_button,
        win.center_button,
        win.derivative_button,
        win.integral_button,
        win.transform_button,
        win.combine_button,
    ]
    for button in dependent_buttons:
        button.set_sensitive(enabled)


def reload_item_menu(self):
    while self.main_window.item_list.get_last_child() is not None:
        self.main_window.item_list.remove(
            self.main_window.item_list.get_last_child())

    for item in self.datadict.values():
        self.main_window.item_list.append(ItemBox(self, item))


def on_confirm_discard_response(_dialog, response, self):
    if response == "discard":
        dialog = Gtk.FileDialog()
        dialog.set_filters(
            utilities.create_file_filters([("Graphs Project File", "graphs")]))
        dialog.set_initial_name("project.graphs")
        dialog.open(self.main_window, None, on_open_project_response, self)


def on_add_data_response(dialog, response, self, import_settings=None):
    try:
        files = dialog.open_multiple_finish(response)
        graphs.open_files(self, files, import_settings)
    except GLib.GError:
        pass


def on_export_data_response(dialog, response, self, multiple):
    try:
        if multiple:
            path = dialog.select_folder_finish(response).peek_path()
        else:
            path = dialog.save_finish(response).peek_path()
        file_io.save_file(self, path)
    except GLib.GError:
        pass


def on_open_project_response(dialog, response, self):
    try:
        path = dialog.open_finish(response).peek_path()
        graphs.open_project(self, path)
    except GLib.GError:
        pass


def on_save_project_response(dialog, response, self):
    try:
        file = dialog.save_finish(response)
        file_io.save_project(
            file.get_path(),
            self.plot_settings,
            self.datadict,
            self.datadict_clipboard,
            self.clipboard_pos,
            self.version)
    except GLib.GError:
        pass


def show_about_window(self):
    developers = [
        "Sjoerd Stendahl <contact@sjoerd.se>",
        "Christoph Kohnen <christoph.kohnen@disroot.org>",
    ]
    about = Adw.AboutWindow(transient_for=self.main_window,
                            application_name=self.name,
                            application_icon=self.appid,
                            website=self.website,
                            developer_name=self.author,
                            issue_url=self.issues,
                            version=self.version,
                            developers=developers,
                            copyright=f"© {self.copyright} {self.author}",
                            license_type="GTK_LICENSE_GPL_3_0")
    whats_new_path = os.path.join(self.pkgdatadir, "whats_new")
    with open(whats_new_path, "r", encoding="utf-8") as file:
        about.set_release_notes(file.read())
    about.present()
