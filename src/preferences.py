# SPDX-License-Identifier: GPL-3.0-or-later
import json
import logging
import os
import shutil

from gi.repository import Adw, Gtk

from graphs import graphs, utilities, plot_styles

from matplotlib.lines import Line2D


class Preferences():
    def __init__(self, parent):
        self.parent = parent
        self.create_new_config_file()
        self.config = self.load_config()
        self.check_config(self.config)

    def check_config(self, config):
        template_path = os.path.join(self.parent.modulepath, "config.json")
        with open(template_path, "r", encoding="utf-8") as file:
            template = json.load(file)
        if set(config.keys()) != set(template.keys()):
            config = utilities.remove_unused_config_keys(config, template)
            config = utilities.add_new_config_keys(config, template)
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
        config = self.check_config(config)
        return config

    def save_config(self):
        config_path = utilities.get_config_path()
        os.chdir(config_path)
        with open("config.json", "w", encoding="utf-8") as file:
            json.dump(self.config, file)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/preferences.ui")
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesWindow"
    selected_line_thickness_slider = Gtk.Template.Child()
    unselected_line_thickness_slider = Gtk.Template.Child()
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
    plot_selected_linestyle_chooser = Gtk.Template.Child()
    plot_unselected_linestyle_chooser = Gtk.Template.Child()
    plot_selected_markers_chooser = Gtk.Template.Child()
    plot_unselected_markers_chooser = Gtk.Template.Child()
    plot_style_dark = Gtk.Template.Child()
    plot_style_light = Gtk.Template.Child()
    plot_legend_check = Gtk.Template.Child()
    plot_title = Gtk.Template.Child()
    plot_color_cycle = Gtk.Template.Child()
    plot_invert_color_cycle_dark = Gtk.Template.Child()
    plot_selected_marker_size = Gtk.Template.Child()
    plot_unselected_marker_size = Gtk.Template.Child()
    center_data_chooser = Gtk.Template.Child()
    handle_duplicates_chooser = Gtk.Template.Child()
    column_x = Gtk.Template.Child()
    column_y = Gtk.Template.Child()
    import_skip_rows = Gtk.Template.Child()
    import_separator = Gtk.Template.Child()
    import_delimiter = Gtk.Template.Child()
    guess_headers = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.props.modal = True
        color_cycles = [
            "Pastel1", "Pastel2", "Paired", "Accent",
            "Dark2", "Set1", "Set2", "Set3",
            "tab10", "tab20", "tab20b", "tab20c"]
        utilities.populate_chooser(self.plot_color_cycle, color_cycles)
        utilities.populate_chooser(
            self.plot_style_dark, plot_styles.get_user_styles(parent).keys())
        utilities.populate_chooser(
            self.plot_style_light, plot_styles.get_user_styles(parent).keys())
        utilities.populate_chooser(self.plot_selected_markers_chooser,
                                   list(Line2D.markers.values()), clear=False)
        utilities.populate_chooser(self.plot_unselected_markers_chooser,
                                   list(Line2D.markers.values()), clear=False)
        self.load_configuration()
        self.connect("close-request", self.on_close, self.parent)
        self.set_transient_for(self.parent.main_window)
        self.present()

    def load_configuration(self):
        config = self.parent.preferences.config
        self.selected_line_thickness_slider.set_range(0.1, 10)
        self.unselected_line_thickness_slider.set_range(0.1, 10)
        self.plot_selected_marker_size.set_range(0, 30)
        self.plot_unselected_marker_size.set_range(0, 30)
        self.addequation_equation.set_text(str(config["addequation_equation"]))
        self.addequation_x_start.set_text(str(config["addequation_x_start"]))
        self.addequation_x_stop.set_text(str(config["addequation_x_stop"]))
        self.addequation_step_size.set_text(
            str(config["addequation_step_size"]))
        self.import_skip_rows.set_value(int(config["import_skip_rows"]))
        self.column_y.set_value(int(config["import_column_y"]))
        self.column_x.set_value(int(config["import_column_x"]))
        self.import_delimiter.set_text(config["import_delimiter"])
        self.plot_selected_marker_size.set_value(
            config["plot_selected_marker_size"])
        self.plot_unselected_marker_size.set_value(
            config["plot_unselected_marker_size"])
        self.unselected_line_thickness_slider.set_value(
            config["unselected_linewidth"])
        self.selected_line_thickness_slider.set_value(
            config["selected_linewidth"])
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
            self.plot_color_cycle, config["plot_color_cycle"])
        utilities.set_chooser(
            self.plot_selected_linestyle_chooser,
            config["plot_selected_linestyle"])
        utilities.set_chooser(
            self.plot_unselected_linestyle_chooser,
            config["plot_unselected_linestyle"])
        utilities.set_chooser(
            self.plot_style_light, config["plot_style_light"])
        utilities.set_chooser(self.plot_style_dark, config["plot_style_dark"])
        marker_dict = Line2D.markers
        unselected_marker_value = \
            marker_dict[config["plot_unselected_markers"]]
        selected_marker_value = \
            marker_dict[config["plot_selected_markers"]]
        utilities.set_chooser(
            self.plot_selected_markers_chooser, selected_marker_value)
        utilities.set_chooser(
            self.plot_unselected_markers_chooser, unselected_marker_value)
        self.guess_headers.set_active(config["guess_headers"])
        self.savefig_transparent_check_button.set_active(
            config["export_figure_transparent"])
        self.plot_legend_check.set_active(config["plot_legend"])
        self.plot_invert_color_cycle_dark.set_active(
            config["plot_invert_color_cycle_dark"])

    def apply_configuration(self):
        config = self.parent.preferences.config
        config["addequation_equation"] = self.addequation_equation.get_text()
        config["addequation_x_start"] = self.addequation_x_start.get_text()
        config["addequation_x_stop"] = self.addequation_x_stop.get_text()
        config["addequation_step_size"] = self.addequation_step_size.get_text()
        selected_marker = self.plot_selected_marker_size
        config["plot_selected_marker_size"] = selected_marker.get_value()
        unselected_marker = self.plot_unselected_marker_size
        config["plot_unselected_marker_size"] = unselected_marker.get_value()
        selected_thickness = self.selected_line_thickness_slider
        config["selected_linewidth"] = selected_thickness.get_value()
        unselected_linewidth = self.unselected_line_thickness_slider
        config["unselected_linewidth"] = unselected_linewidth.get_value()
        config["guess_headers"] = self.guess_headers.get_active()
        config["handle_duplicates"] = \
            self.handle_duplicates_chooser.get_selected_item().get_string()
        config["export_figure_transparent"] = \
            self.savefig_transparent_check_button.get_active()
        config["plot_legend"] = self.plot_legend_check.get_active()
        config["plot_invert_color_cycle_dark"] = \
            self.plot_invert_color_cycle_dark.get_active()
        config["plot_y_label"] = self.plot_y_label.get_text()
        config["plot_x_label"] = self.plot_x_label.get_text()
        config["plot_right_label"] = self.plot_right_label.get_text()
        config["plot_top_label"] = self.plot_top_label.get_text()
        config["plot_title"] = self.plot_title.get_text()
        filetype = self.savefig_filetype_chooser
        config["savefig_filetype"] = filetype.get_selected_item().get_string()
        config["plot_color_cycle"] = \
            self.plot_color_cycle.get_selected_item().get_string()
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
        selected_linestyle = self.plot_selected_linestyle_chooser
        config["plot_selected_linestyle"] = \
            selected_linestyle.get_selected_item().get_string()
        unselected_line = self.plot_unselected_linestyle_chooser
        config["plot_unselected_linestyle"] = \
            unselected_line.get_selected_item().get_string()
        config["plot_style_dark"] = \
            self.plot_style_dark.get_selected_item().get_string()
        config["plot_style_light"] = \
            self.plot_style_light.get_selected_item().get_string()
        config["import_column_x"] = int(self.column_x.get_value())
        config["import_column_y"] = int(self.column_y.get_value())
        config["import_skip_rows"] = int(self.import_skip_rows.get_value())
        config["import_separator"] = \
            self.import_separator.get_selected_item().get_string()
        config["import_delimiter"] = self.import_delimiter.get_text()
        marker_dict = Line2D.markers
        unselected_marker_value = utilities.get_dict_by_value(
            marker_dict,
            self.plot_unselected_markers_chooser.get_selected_item(
            ).get_string())
        selected_marker_value = utilities.get_dict_by_value(
            marker_dict, self.plot_selected_markers_chooser.get_selected_item(
            ).get_string())
        config["plot_unselected_markers"] = unselected_marker_value
        config["plot_selected_markers"] = selected_marker_value

    def on_close(self, _, parent):
        self.apply_configuration()
        parent.preferences.save_config()
        graphs.reload(parent)
