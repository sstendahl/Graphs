# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk

from graphs import styles, ui


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/preferences.ui")
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesWindow"
    general_center = Gtk.Template.Child()
    general_handle_duplicates = Gtk.Template.Child()
    general_hide_unselected = Gtk.Template.Child()
    general_override_item_properties = Gtk.Template.Child()
    figure_title = Gtk.Template.Child()
    figure_bottom_label = Gtk.Template.Child()
    figure_left_label = Gtk.Template.Child()
    figure_top_label = Gtk.Template.Child()
    figure_right_label = Gtk.Template.Child()
    figure_bottom_scale = Gtk.Template.Child()
    figure_left_scale = Gtk.Template.Child()
    figure_top_scale = Gtk.Template.Child()
    figure_right_scale = Gtk.Template.Child()
    figure_x_position = Gtk.Template.Child()
    figure_y_position = Gtk.Template.Child()
    figure_legend = Gtk.Template.Child()
    figure_legend_position = Gtk.Template.Child()
    figure_use_custom_style = Gtk.Template.Child()
    figure_custom_style = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(
            application=application, transient_for=application.get_window(),
        )

        styles_ = sorted(styles.get_user_styles(application).keys())
        self.figure_custom_style.set_model(Gtk.StringList.new(styles_))
        settings = self.get_application().get_settings()
        ui.bind_values_to_settings(
            settings.get_child("figure"), self, prefix="figure_",
            ignorelist=["custom-style"])
        ui.bind_values_to_settings(
            settings.get_child("general"), self, prefix="general_")
        self.figure_custom_style.set_selected(styles_.index(
            settings.get_child("figure").get_string("custom-style")))
        self.present()

    @Gtk.Template.Callback()
    def on_close(self, _ignored):
        self.destroy()

    @Gtk.Template.Callback()
    def on_custom_style_select(self, comborow, _ignored):
        self.get_application().get_settings("figure").set_string(
            "custom-style", comborow.get_selected_item().get_string(),
        )
