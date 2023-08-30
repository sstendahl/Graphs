# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk

from graphs import ui


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/preferences.ui")
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesWindow"
    general_center = Gtk.Template.Child()
    general_handle_duplicates = Gtk.Template.Child()
    general_hide_unselected = Gtk.Template.Child()
    general_override_item_properties = Gtk.Template.Child()
    general_x_position = Gtk.Template.Child()
    general_y_position = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(
            application=application, transient_for=application.get_window(),
        )
        ui.bind_values_to_settings(
            self.get_application().get_settings("general"),
            self, prefix="general_",
        )
        self.present()

    @Gtk.Template.Callback()
    def on_close(self, _ignored):
        self.destroy()
