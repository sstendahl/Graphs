# SPDX-License-Identifier: GPL-3.0-or-later
import os
import pathlib

from gi.repository import Adw, Gtk, GLib, Gio

from graphs import file_io, graphs


def toggle_darkmode(_shortcut, _theme, _widget, self):
    if Adw.StyleManager.get_default().get_dark():
        self.plot_settings.plot_style = self.preferences.config[
            "plot_style_dark"]
    else:
        self.plot_settings.plot_style = self.preferences.config[
            "plot_style_light"]
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


def on_confirm_discard_response(_dialog, response, self):
    if response == "discard":
        chooser = self.build("dialogs", "open_project")
        chooser.set_transient_for(self.main_window)
        chooser.connect("response", on_open_response, self, True)
        chooser.show()


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
        path = dialog.save_finish(response).peek_path()
        file_io.save_project(
            path,
            self.plot_settings,
            self.datadict,
            self.version)
    except GLib.GError:
        pass


def show_about_window(self):
    developers = [
        "Sjoerd Broekhuijsen <contact@sjoerd.se>",
        "Christoph Kohnen <christoph.kohnen@disroot.org>"
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
    path = os.getenv("XDG_DATA_DIRS").split(":")[0]
    with open(os.path.join(
            path + "/graphs/graphs/whats_new"), "r", encoding="utf-8") as file:
        about.set_release_notes(file.read())
    about.present()
