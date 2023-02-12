# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import GLib, Adw, Gtk

from . import plotting_tools, file_io, graphs

def toggle_sidebar(action, shortcut, self):
    flap = self.main_window.sidebar_flap
    enabled = not flap.get_reveal_flap()
    action.change_state(GLib.Variant.new_boolean(enabled))
    flap.set_reveal_flap(enabled)

def toggle_darkmode(shortcut, theme, widget, self):
    if Adw.StyleManager.get_default().get_dark():
        self.plot_settings.plot_style = self.preferences.config["plot_style_dark"]
    else:
        self.plot_settings.plot_style = self.preferences.config["plot_style_light"]
    plotting_tools.reload_plot(self)

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
    win.center_data_button,
    win.derivative_button,
    win.integral_button,
    win.transform_data_button,
    win.combine_data_button,
    ]

    for button in dependent_buttons:
        button.set_sensitive(enabled)

def disable_clipboard_buttons(self):
    win = self.main_window
    win.redo_button.set_sensitive(False)
    win.undo_button.set_sensitive(False)

def open_file_dialog(widget, _, self, open_project):
    open_file_chooser = Gtk.FileChooserNative.new(
        title="Open new files",
        parent=self.main_window,
        action=Gtk.FileChooserAction.OPEN,
        accept_label="_Open",
    )
    open_file_chooser.set_modal(True)
    open_file_chooser.set_select_multiple(open_project)
    open_file_chooser.connect("response", on_open_file_response, self, open_project)
    open_file_chooser.show()

def on_open_file_response(dialog, response, self, project):
    if response == Gtk.ResponseType.ACCEPT:
        if(project):
            file_io.load_project(self, dialog.get_files())
        else:
            graphs.open_files(self, dialog.get_files())

def save_project_dialog(widget, _, self, documenttype="Graphs Project (*)"):
    def save_project_chooser(action):
        dialog = Gtk.FileChooserNative.new(
            title="Save files",
            parent=self.main_window,
            action=action,
            accept_label="_Save",
        )
        return dialog

    chooser = save_project_chooser(Gtk.FileChooserAction.SAVE)
    chooser.set_modal(True)
    chooser.connect("response", on_save_response, self, True)
    chooser.show()

def save_file_dialog(self, documenttype="Text file (*.txt)"):
    def save_file_chooser(action):
        dialog = Gtk.FileChooserNative.new(
            title="Save files",
            parent=self.main_window,
            action=action,
            accept_label="_Save",
        )
        return dialog

    if len(self.datadict) == 1:
        chooser = save_file_chooser(Gtk.FileChooserAction.SAVE)
    elif len(self.datadict) > 1:
        chooser = save_file_chooser(Gtk.FileChooserAction.SELECT_FOLDER)

    if len(self.datadict) == 1:
        filename = list(self.datadict.values())[0].filename
        chooser.set_current_name(f"{filename}.txt")
    try:
        chooser.set_modal(True)
        chooser.connect("response", on_save_response, self, False)
        chooser.show()
    except UnboundLocalError:
        self.main_window.toast_overlay.add_toast(Adw.Toast(title=f"Could not open save dialog, make sure you have data opened"))

def on_save_response(dialog, response, self, project):
    if response == Gtk.ResponseType.ACCEPT:
        path = dialog.get_file().peek_path()
        if project:
            file_io.save_project(self, path)
        else:
            file_io.save_file(self, path)
