# SPDX-License-Identifier: GPL-3.0-or-later
import json
import logging
import os
import shutil

from gi.repository import Adw, Gtk

from graphs import graphs, plot_styles, utilities


class Preferences():
    def __init__(self, parent):
        self.parent = parent
        self.create_new_config_file()
        self.config = self.load_config()
        self.check_config(self.config)

    def check_config(self, config):
        template_path = os.path.join(self.parent.modulepath, "config.json")
        with open(template_path, "r", encoding="utf-8") as file:
            self.template = json.load(file)
        if set(config.keys()) != set(self.template.keys()):
            config = utilities.remove_unused_config_keys(config, self.template)
            config = utilities.add_new_config_keys(config, self.template)
        return config

    def create_new_config_file(self):
        config_path = utilities.get_config_path()
        if not os.path.isfile(f"{config_path}/config.json"):
            self.reset_config()
            logging.info("New configuration file created")
        else:
            logging.debug("Loading configuration file")

    def reset_config(self):
        config_path = utilities.get_config_path()
        old_path = self.parent.modulepath
        if not os.path.isdir(config_path):
            os.mkdir(config_path)
        path = config_path + "/config.json"
        shutil.copy(f"{old_path}/config.json", path)
        logging.debug("Loaded new config")

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
    savefig_transparent_check_button = Gtk.Template.Child()
    savefig_filetype_chooser = Gtk.Template.Child()
    savefig_filetype_list = Gtk.Template.Child()
    addequation_equation = Gtk.Template.Child()
    addequation_x_start = Gtk.Template.Child()
    addequation_x_stop = Gtk.Template.Child()
    addequation_step_size = Gtk.Template.Child()
    plot_y_label = Gtk.Template.Child()
    plot_x_label = Gtk.Template.Child()
    plot_right_label = Gtk.Template.Child()
    plot_top_label = Gtk.Template.Child()
    plot_y_position = Gtk.Template.Child()
    plot_x_position = Gtk.Template.Child()
    plot_x_scale = Gtk.Template.Child()
    plot_y_scale = Gtk.Template.Child()
    plot_top_scale = Gtk.Template.Child()
    plot_right_scale = Gtk.Template.Child()
    use_custom_plot_style = Gtk.Template.Child()
    custom_plot_style = Gtk.Template.Child()
    plot_legend_check = Gtk.Template.Child()
    plot_title = Gtk.Template.Child()
    center_data_chooser = Gtk.Template.Child()
    handle_duplicates_chooser = Gtk.Template.Child()
    column_x = Gtk.Template.Child()
    column_y = Gtk.Template.Child()
    import_skip_rows = Gtk.Template.Child()
    import_separator = Gtk.Template.Child()
    import_delimiter = Gtk.Template.Child()
    guess_headers = Gtk.Template.Child()
    hide_unselected = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        utilities.populate_chooser(
            self.custom_plot_style, plot_styles.get_user_styles(parent).keys())
        self.load_configuration()
        self.connect("close-request", self.on_close, self.parent)
        self.set_transient_for(self.parent.main_window)
        self.present()

    def load_configuration(self):
        config = self.parent.preferences.config
        self.addequation_equation.set_text(str(config["addequation_equation"]))
        self.addequation_x_start.set_text(str(config["addequation_x_start"]))
        self.addequation_x_stop.set_text(str(config["addequation_x_stop"]))
        self.addequation_step_size.set_text(
            str(config["addequation_step_size"]))
        self.import_skip_rows.set_value(int(config["import_skip_rows"]))
        self.column_y.set_value(int(config["import_column_y"]))
        self.column_x.set_value(int(config["import_column_x"]))
        self.import_delimiter.set_text(config["import_delimiter"])
        self.plot_y_label.set_text(config["plot_y_label"])
        self.plot_x_label.set_text(config["plot_x_label"])
        self.plot_right_label.set_text(config["plot_right_label"])
        self.plot_top_label.set_text(config["plot_top_label"])
        self.plot_title.set_text(config["plot_title"])
        utilities.set_chooser(
            self.savefig_filetype_chooser, config["savefig_filetype"])
        utilities.set_chooser(
            self.center_data_chooser, config["action_center_data"])
        utilities.set_chooser(
            self.plot_x_scale, config["plot_x_scale"])
        utilities.set_chooser(
            self.plot_top_scale, config["plot_top_scale"])
        utilities.set_chooser(
            self.plot_right_scale, config["plot_right_scale"])
        utilities.set_chooser(
            self.plot_y_scale, config["plot_y_scale"])
        utilities.set_chooser(
            self.plot_x_position, config["plot_x_position"])
        utilities.set_chooser(
            self.plot_y_position, config["plot_y_position"])
        utilities.set_chooser(
            self.handle_duplicates_chooser, config["handle_duplicates"])
        utilities.set_chooser(
            self.import_separator, config["import_separator"])
        utilities.set_chooser(
            self.custom_plot_style, config["custom_plot_style"])
        self.use_custom_plot_style.set_enable_expansion(
            config["use_custom_plot_style"])
        self.guess_headers.set_active(config["guess_headers"])
        self.savefig_transparent_check_button.set_active(
            config["export_figure_transparent"])
        self.plot_legend_check.set_active(config["plot_legend"])
        self.hide_unselected.set_active(config["hide_unselected"])

    def apply_configuration(self):
        config = self.parent.preferences.config
        config["addequation_equation"] = self.addequation_equation.get_text()
        config["addequation_x_start"] = self.addequation_x_start.get_text()
        config["addequation_x_stop"] = self.addequation_x_stop.get_text()
        config["addequation_step_size"] = self.addequation_step_size.get_text()
        config["guess_headers"] = self.guess_headers.get_active()
        config["handle_duplicates"] = \
            self.handle_duplicates_chooser.get_selected_item().get_string()
        config["export_figure_transparent"] = \
            self.savefig_transparent_check_button.get_active()
        config["plot_legend"] = self.plot_legend_check.get_active()
        config["hide_unselected"] = self.hide_unselected.get_active()
        config["plot_y_label"] = self.plot_y_label.get_text()
        config["plot_x_label"] = self.plot_x_label.get_text()
        config["plot_right_label"] = self.plot_right_label.get_text()
        config["plot_top_label"] = self.plot_top_label.get_text()
        config["plot_title"] = self.plot_title.get_text()
        filetype = self.savefig_filetype_chooser
        config["savefig_filetype"] = filetype.get_selected_item().get_string()
        config["plot_x_scale"] = \
            self.plot_x_scale.get_selected_item().get_string()
        config["plot_y_scale"] = \
            self.plot_y_scale.get_selected_item().get_string()
        config["plot_top_scale"] = \
            self.plot_top_scale.get_selected_item().get_string()
        config["plot_right_scale"] = \
            self.plot_right_scale.get_selected_item().get_string()
        config["plot_right_scale"] = \
            self.plot_right_scale.get_selected_item().get_string()
        config["plot_top_scale"] = \
            self.plot_top_scale.get_selected_item().get_string()
        config["plot_x_position"] = \
            self.plot_x_position.get_selected_item().get_string()
        config["plot_y_position"] = \
            self.plot_y_position.get_selected_item().get_string()
        config["action_center_data"] = \
            self.center_data_chooser.get_selected_item().get_string()
        config["use_custom_plot_style"] = \
            self.use_custom_plot_style.get_enable_expansion()
        config["custom_plot_style"] = \
            self.custom_plot_style.get_selected_item().get_string()
        config["import_column_x"] = int(self.column_x.get_value())
        config["import_column_y"] = int(self.column_y.get_value())
        config["import_skip_rows"] = int(self.import_skip_rows.get_value())
        config["import_separator"] = \
            self.import_separator.get_selected_item().get_string()
        config["import_delimiter"] = self.import_delimiter.get_text()

    def on_close(self, _, parent):
        self.apply_configuration()
        parent.preferences.save_config()
        graphs.reload(parent)
