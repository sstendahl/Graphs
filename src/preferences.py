# SPDX-License-Identifier: GPL-3.0-or-later
import json
import logging
import os
from gettext import gettext as _

from gi.repository import Adw, Gio, Gtk

from graphs import graphs, plot_styles, utilities


class Preferences():
    def __init__(self, parent):
        self.parent = parent
        self.create_new_config_file()
        self.config = self.load_config()
        self.check_config(self.config)

    def check_config(self, config):
        template_file = Gio.File.new_for_uri(
            "resource:///se/sjoerd/Graphs/config.json")
        template = json.loads(
            template_file.read(None).read_bytes(8192, None).get_data())
        if set(config.keys()) != set(template.keys()):
            config = utilities.remove_unused_config_keys(config, template)
            config = utilities.add_new_config_keys(config, template)
        return config

    def create_new_config_file(self):
        config_path = os.path.join(utilities.get_config_path(), "config.json")
        if not os.path.isfile(config_path):
            self.reset_config()
            logging.info(_("New configuration file created"))
        else:
            logging.debug(_("Loading configuration file"))

    def reset_config(self):
        config_path = utilities.get_config_path()
        if not os.path.isdir(config_path):
            os.mkdir(config_path)
        template_file = Gio.File.new_for_uri(
            "resource:///se/sjoerd/Graphs/config.json")
        config_file = Gio.File.new_for_path(
            os.path.join(config_path, "config.json"))
        template_file.copy(config_file, Gio.FileCopyFlags(1), None, None, None)
        logging.debug(_("Loaded new config"))

    def load_config(self):
        config_path = utilities.get_config_path()
        os.chdir(config_path)
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        return self.check_config(config)

    def save_config(self):
        config_path = utilities.get_config_path()
        os.chdir(config_path)
        with open("config.json", "w", encoding="utf-8") as file:
            json.dump(self.config, file)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/preferences.ui")
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesWindow"
    clipboard_length = Gtk.Template.Child()
    import_delimiter = Gtk.Template.Child()
    import_separator = Gtk.Template.Child()
    import_column_x = Gtk.Template.Child()
    import_column_y = Gtk.Template.Child()
    import_skip_rows = Gtk.Template.Child()
    addequation_equation = Gtk.Template.Child()
    addequation_x_start = Gtk.Template.Child()
    addequation_x_stop = Gtk.Template.Child()
    addequation_step_size = Gtk.Template.Child()
    export_figure_dpi = Gtk.Template.Child()
    export_figure_filetype = Gtk.Template.Child()
    export_figure_transparent = Gtk.Template.Child()
    action_center_data = Gtk.Template.Child()
    other_handle_duplicates = Gtk.Template.Child()
    other_hide_unselected = Gtk.Template.Child()
    override_style_change = Gtk.Template.Child()
    plot_title = Gtk.Template.Child()
    plot_x_label = Gtk.Template.Child()
    plot_y_label = Gtk.Template.Child()
    plot_top_label = Gtk.Template.Child()
    plot_right_label = Gtk.Template.Child()
    plot_guess_headers = Gtk.Template.Child()
    plot_x_scale = Gtk.Template.Child()
    plot_y_scale = Gtk.Template.Child()
    plot_top_scale = Gtk.Template.Child()
    plot_right_scale = Gtk.Template.Child()
    plot_x_position = Gtk.Template.Child()
    plot_y_position = Gtk.Template.Child()
    plot_legend = Gtk.Template.Child()
    plot_legend_position = Gtk.Template.Child()
    plot_use_custom_style = Gtk.Template.Child()
    plot_custom_style = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        utilities.populate_chooser(
            self.plot_custom_style, plot_styles.get_user_styles(parent).keys())
        self.load_configuration()
        self.connect("close-request", self.on_close, self.parent)
        self.set_transient_for(self.parent.main_window)
        self.present()

    def load_configuration(self):
        config = self.parent.preferences.config
        self.clipboard_length.set_value(int(config["clipboard_length"]))
        self.import_delimiter.set_text(config["import_delimiter"])
        utilities.set_chooser(
            self.import_separator, config["import_separator"])
        self.import_column_x.set_value(int(config["import_column_x"]))
        self.import_column_y.set_value(int(config["import_column_y"]))
        self.import_skip_rows.set_value(int(config["import_skip_rows"]))
        self.addequation_equation.set_text(str(config["addequation_equation"]))
        self.addequation_x_start.set_text(str(config["addequation_x_start"]))
        self.addequation_x_stop.set_text(str(config["addequation_x_stop"]))
        self.addequation_step_size.set_text(
            str(config["addequation_step_size"]))
        self.export_figure_dpi.set_value(int(config["export_figure_dpi"]))
        utilities.set_chooser(
            self.export_figure_filetype, config["export_figure_filetype"])
        self.export_figure_transparent.set_active(
            config["export_figure_transparent"])
        utilities.set_chooser(
            self.action_center_data, config["action_center_data"])
        utilities.set_chooser(
            self.other_handle_duplicates, config["handle_duplicates"])
        self.other_hide_unselected.set_active(config["hide_unselected"])
        self.override_style_change.set_active(config["override_style_change"])
        self.plot_title.set_text(config["plot_title"])
        self.plot_x_label.set_text(config["plot_x_label"])
        self.plot_y_label.set_text(config["plot_y_label"])
        self.plot_top_label.set_text(config["plot_top_label"])
        self.plot_right_label.set_text(config["plot_right_label"])
        self.plot_guess_headers.set_active(config["guess_headers"])
        utilities.set_chooser(
            self.plot_x_scale, config["plot_x_scale"])
        utilities.set_chooser(
            self.plot_y_scale, config["plot_y_scale"])
        utilities.set_chooser(
            self.plot_top_scale, config["plot_top_scale"])
        utilities.set_chooser(
            self.plot_right_scale, config["plot_right_scale"])
        utilities.set_chooser(
            self.plot_x_position, config["plot_x_position"])
        utilities.set_chooser(
            self.plot_y_position, config["plot_y_position"])
        utilities.set_chooser(
            self.plot_legend_position,
            config["plot_legend_position"].capitalize())
        self.plot_legend.set_enable_expansion(config["plot_legend"])
        self.plot_use_custom_style.set_enable_expansion(
            config["plot_use_custom_style"])
        utilities.set_chooser(
            self.plot_custom_style, config["plot_custom_style"])

    def apply_configuration(self):
        config = self.parent.preferences.config
        config["import_delimiter"] = self.import_delimiter.get_text()
        config["import_separator"] = \
            self.import_separator.get_selected_item().get_string()
        config["import_column_x"] = int(self.import_column_x.get_value())
        config["import_column_y"] = int(self.import_column_y.get_value())
        config["import_skip_rows"] = int(self.import_skip_rows.get_value())
        config["addequation_equation"] = self.addequation_equation.get_text()
        config["addequation_x_start"] = self.addequation_x_start.get_text()
        config["addequation_x_stop"] = self.addequation_x_stop.get_text()
        config["addequation_step_size"] = self.addequation_step_size.get_text()
        config["clipboard_length"] = int(self.clipboard_length.get_value())
        config["export_figure_dpi"] = int(self.export_figure_dpi.get_value())
        config["export_figure_filetype"] = \
            self.export_figure_filetype.get_selected_item().get_string()
        config["export_figure_transparent"] = \
            self.export_figure_transparent.get_active()
        config["action_center_data"] = \
            self.action_center_data.get_selected_item().get_string()
        config["handle_duplicates"] = \
            self.other_handle_duplicates.get_selected_item().get_string()
        config["hide_unselected"] = self.other_hide_unselected.get_active()
        config["override_style_change"] = \
            self.override_style_change.get_active()
        config["plot_title"] = self.plot_title.get_text()
        config["plot_x_label"] = self.plot_x_label.get_text()
        config["plot_y_label"] = self.plot_y_label.get_text()
        config["plot_top_label"] = self.plot_top_label.get_text()
        config["plot_right_label"] = self.plot_right_label.get_text()
        config["guess_headers"] = self.plot_guess_headers.get_active()
        config["plot_x_scale"] = \
            self.plot_x_scale.get_selected_item().get_string()
        config["plot_y_scale"] = \
            self.plot_y_scale.get_selected_item().get_string()
        config["plot_top_scale"] = \
            self.plot_top_scale.get_selected_item().get_string()
        config["plot_right_scale"] = \
            self.plot_right_scale.get_selected_item().get_string()
        config["plot_x_position"] = \
            self.plot_x_position.get_selected_item().get_string()
        config["plot_y_position"] = \
            self.plot_y_position.get_selected_item().get_string()
        config["plot_legend"] = self.plot_legend.get_enable_expansion()
        config["plot_legend_position"] = \
            self.plot_legend_position.get_selected_item().get_string().lower()
        config["plot_use_custom_style"] = \
            self.plot_use_custom_style.get_enable_expansion()
        config["plot_custom_style"] = \
            self.plot_custom_style.get_selected_item().get_string()

    def on_close(self, _, parent):
        self.apply_configuration()
        parent.preferences.save_config()
        graphs.reload(parent)
