# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, Gio, Gtk

from graphs import file_io, graphs, misc, plot_styles, ui, utilities


MIGRATION_KEYS = {
    # new: old
    "other_handle_duplicates": "handle_duplicates",
    "other_hide_unselected": "hide_unselected",
}


def _validate(config: dict, template: dict):
    """
    Validates a given dictionary against a template, such that they
    remain compatible with updated versions of Graphs. If the key in the
    dictionary is not present in the template due to an update, the key will
    be updated using MIGRATION_KEYS.

    If the template or validated key does not match with the MIGRATION_KEYS,
    the template keys and their associated values will be used instead for
    the validated dictionary.

    Args:
        config: Dictionary to be validated
        template: Template dictionary to which the config is validated against
    Returns:
        dict: Validated dictionary
    """
    return {key: config[key if key in config else MIGRATION_KEYS[key]]
            if key in config
            or (key in MIGRATION_KEYS and MIGRATION_KEYS[key] in config)
            else value for key, value in template.items()}


class Preferences(dict):
    def __init__(self):
        config_dir = utilities.get_config_directory()
        if not config_dir.query_exists(None):
            config_dir.make_directory_with_parents(None)
        config_file = config_dir.get_child_for_display_name("config.json")
        import_file = config_dir.get_child_for_display_name("import.json")
        template_config_file = Gio.File.new_for_uri(
            "resource:///se/sjoerd/Graphs/config.json")
        template_import_file = Gio.File.new_for_uri(
            "resource:///se/sjoerd/Graphs/import.json")
        if not config_file.query_exists(None):
            template_config_file.copy(
                config_file, Gio.FileCopyFlags(1), None, None, None)
            logging.info(_("New configuration file created"))
        if not import_file.query_exists(None):
            template_import_file.copy(
                import_file, Gio.FileCopyFlags(1), None, None, None)
            logging.info(_("New Import Settings file created"))

        super().update(_validate(
            file_io.parse_json(config_file),
            file_io.parse_json(template_config_file)))

        import_params_template = file_io.parse_json(template_import_file)
        self["import_params"] = _validate({
            key: _validate(item, import_params_template[key])
            for key, item in file_io.parse_json(import_file).items()
        }, import_params_template)

    def update(self, values: dict):
        super().update(values)
        self.save()

    def update_modes(self, values: dict):
        for mode, params in values.items():
            self["import_params"][mode].update(params)
        self.save()

    def save(self):
        config_dir = utilities.get_config_directory()
        config = self.copy()
        file_io.write_json(
            config_dir.get_child_for_display_name("import.json"),
            config["import_params"])
        del config["import_params"]
        file_io.write_json(
            config_dir.get_child_for_display_name("config.json"),
            config)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/preferences.ui")
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesWindow"
    general_center_data = Gtk.Template.Child()
    general_handle_duplicates = Gtk.Template.Child()
    general_hide_unselected = Gtk.Template.Child()
    general_override_item_properties = Gtk.Template.Child()
    plot_title = Gtk.Template.Child()
    plot_bottom_label = Gtk.Template.Child()
    plot_left_label = Gtk.Template.Child()
    plot_top_label = Gtk.Template.Child()
    plot_right_label = Gtk.Template.Child()
    plot_bottom_scale = Gtk.Template.Child()
    plot_left_scale = Gtk.Template.Child()
    plot_top_scale = Gtk.Template.Child()
    plot_right_scale = Gtk.Template.Child()
    plot_x_position = Gtk.Template.Child()
    plot_y_position = Gtk.Template.Child()
    plot_legend = Gtk.Template.Child()
    plot_legend_position = Gtk.Template.Child()
    plot_use_custom_style = Gtk.Template.Child()
    plot_custom_style = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(application=application,
                         transient_for=application.main_window)

        utilities.populate_chooser(
            self.general_center_data, misc.ACTION_CENTER_DATA)
        utilities.populate_chooser(
            self.general_handle_duplicates, misc.HANDLE_DUPLICATES)
        utilities.populate_chooser(self.plot_bottom_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_left_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_top_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_right_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_x_position, misc.X_POSITIONS)
        utilities.populate_chooser(self.plot_y_position, misc.Y_POSITIONS)
        utilities.populate_chooser(
            self.plot_legend_position, misc.LEGEND_POSITIONS)

        utilities.populate_chooser(
            self.plot_custom_style,
            plot_styles.get_user_styles(self.props.application).keys(),
            translate=False)
        settings = self.props.application.settings
        ui.bind_values_to_settings(
            settings.get_child("figure"), self, prefix="plot_")
        ui.bind_values_to_settings(
            settings, self, prefix="general_", ignorelist=["clipboard-length"])
        self.present()

    @Gtk.Template.Callback()
    def on_close(self, _):
        graphs.refresh(self.props.application)
