from gi.repository import Gtk, Adw, GObject
import os
import shutil
from . import plotting_tools, datman
import json
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.font_manager

def open_preferences_window(widget, _, self):
    win = PreferencesWindow(self)
    self.preferences.load_config()
    win.present()


class Preferences():
    def __init__(self):
        self.create_new_config_file()
        self.config = self.load_config()

    def create_new_config_file(self):
        config_path = self.get_config_path()
        old_path = os.path.join(os.getenv("XDG_DATA_DIRS"))
        old_path = old_path.split(":")[0] + "/datman/datman"
        if not os.path.isfile(f"{config_path}/config.json"):
            if not os.path.isdir(config_path):
                os.mkdir(config_path)
            path = config_path + "/config.json"
            shutil.copy(f"{old_path}/config.json", path)
            print(f"No configuration file found, new file is created at {config_path}")
        else:
            print("Loading configuration file")


    def load_config(self):
        config_path = self.get_config_path()
        os.chdir(config_path)
        with open("config.json", 'r') as f:
            config = json.load(f)
        return config

    def save_config(self):
        config_path = self.get_config_path()
        os.chdir(config_path)
        with open("config.json", 'w') as f:
            json.dump(self.config, f)


    def get_config_path(self) -> str:
        if os.getenv("XDG_CONFIG_HOME"):
            return os.path.join(os.getenv("XDG_CONFIG_HOME"), "DatMan")
        else:
            return os.path.join(str(Path.home()), ".local", "share", "DatMan")


@Gtk.Template(resource_path="/se/sjoerd/DatMan/preferences.ui")
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesWindow"
    selected_line_thickness_slider = Gtk.Template.Child()
    unselected_line_thickness_slider = Gtk.Template.Child()
    savefig_transparent_check_button = Gtk.Template.Child()
    savefig_filetype_chooser = Gtk.Template.Child()
    savefig_filetype_list = Gtk.Template.Child()
    plot_Y_label = Gtk.Template.Child()
    plot_X_label = Gtk.Template.Child()
    plot_X_scale = Gtk.Template.Child()
    plot_Y_scale = Gtk.Template.Child()
    plot_selected_linestyle_chooser = Gtk.Template.Child()
    plot_unselected_linestyle_chooser = Gtk.Template.Child()
    plot_selected_markers_chooser = Gtk.Template.Child()
    plot_unselected_markers_chooser = Gtk.Template.Child()
    plot_style_dark = Gtk.Template.Child()
    plot_style_light = Gtk.Template.Child()
    plot_tick_direction = Gtk.Template.Child()
    plot_major_tick_width = Gtk.Template.Child()
    plot_minor_tick_width = Gtk.Template.Child()
    plot_major_tick_length = Gtk.Template.Child()
    plot_minor_tick_length = Gtk.Template.Child()
    plot_legend_check = Gtk.Template.Child()
    plot_title = Gtk.Template.Child()
    plot_color_cycle = Gtk.Template.Child()
    plot_invert_color_cycle_dark = Gtk.Template.Child()
    plot_tick_left = Gtk.Template.Child()
    plot_tick_right = Gtk.Template.Child()
    plot_tick_top = Gtk.Template.Child()
    plot_tick_bottom = Gtk.Template.Child()
    plot_selected_marker_size = Gtk.Template.Child()
    plot_unselected_marker_size = Gtk.Template.Child()
    plot_font_chooser = Gtk.Template.Child()
    center_data_chooser = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.props.modal = True
        color_cycles =  [
            'Pastel1', 'Pastel2', 'Paired', 'Accent',
            'Dark2', 'Set1', 'Set2', 'Set3',
            'tab10', 'tab20', 'tab20b', 'tab20c']
        self.populate_chooser(self.plot_color_cycle, color_cycles)
       # self.populate_chooser(self.plot_font_chooser, self.get_available_fonts())
        self.populate_chooser(self.plot_style_dark, plt.style.available)
        self.populate_chooser(self.plot_style_light, plt.style.available)
        self.populate_chooser(self.plot_selected_markers_chooser, list(Line2D.markers.values()))
        self.populate_chooser(self.plot_unselected_markers_chooser, list(Line2D.markers.values()))
        config = parent.preferences.config
        config = self.load_configuration(config)
        self.connect("close-request", self.on_close, parent)

    def set_chooser(self, chooser, choice):
        model = chooser.get_model()
        for index, option in enumerate(model):
            if option.get_string() == choice:
                chooser.set_selected(index)

    def populate_chooser(self, chooser, chooser_list):
        model = chooser.get_model()
        for item in chooser_list:
            if item != "nothing":
                model.append(str(item))

    def load_configuration(self, config):
        font_string = config["plot_font_string"]
        font_desc = self.plot_font_chooser.get_font_desc().from_string(font_string)
        self.plot_font_chooser.set_font_desc(font_desc)
        self.plot_font_chooser.set_use_font(True)
        self.selected_line_thickness_slider.set_range(0.1, 10)
        self.unselected_line_thickness_slider.set_range(0.1, 10)
        self.plot_major_tick_width.set_range(0, 4)
        self.plot_minor_tick_width.set_range(0, 4)
        self.plot_major_tick_length.set_range(0, 20)
        self.plot_minor_tick_length.set_range(0, 20)
        self.plot_selected_marker_size.set_range(0, 30)
        self.plot_unselected_marker_size.set_range(0, 30)
        self.plot_selected_marker_size.set_value(config["plot_selected_marker_size"])
        self.plot_unselected_marker_size.set_value(config["plot_unselected_marker_size"])
        self.unselected_line_thickness_slider.set_value(config["unselected_linewidth"])
        self.selected_line_thickness_slider.set_value(config["selected_linewidth"])
        self.plot_minor_tick_width.set_value(config["plot_minor_tick_width"])
        self.plot_major_tick_width.set_value(config["plot_major_tick_width"])
        self.plot_minor_tick_length.set_value(config["plot_minor_tick_length"])
        self.plot_major_tick_length.set_value(config["plot_major_tick_length"])
        self.plot_Y_label.set_text(config["plot_Y_label"])
        self.plot_X_label.set_text(config["plot_X_label"])
        self.plot_title.set_text(config["plot_title"])
        self.set_chooser(self.savefig_filetype_chooser, config["savefig_filetype"])
        self.set_chooser(self.center_data_chooser, config["center_data"])
        self.set_chooser(self.plot_X_scale, config["plot_X_scale"])
        self.set_chooser(self.plot_Y_scale, config["plot_Y_scale"])
     #   self.set_chooser(self.plot_font_chooser, config["plot_font_family"])
        self.set_chooser(self.plot_color_cycle, config["plot_color_cycle"])
        self.set_chooser(self.plot_selected_linestyle_chooser, config["plot_selected_linestyle"])
        self.set_chooser(self.plot_unselected_linestyle_chooser, config["plot_unselected_linestyle"])
        self.set_chooser(self.plot_tick_direction, config["plot_tick_direction"])
        self.set_chooser(self.plot_style_light, config["plot_style_light"])
        self.set_chooser(self.plot_style_dark, config["plot_style_dark"])
        marker_dict = Line2D.markers
        unselected_marker_value = marker_dict[config["plot_unselected_markers"]]
        selected_marker_value = marker_dict[config["plot_selected_markers"]]
        self.set_chooser(self.plot_selected_markers_chooser, selected_marker_value)
        self.set_chooser(self.plot_unselected_markers_chooser, unselected_marker_value)
        if config["plot_tick_left"]:
            self.plot_tick_left.set_active(True)
        if config["plot_tick_right"]:
            self.plot_tick_right.set_active(True)
        if config["plot_tick_bottom"]:
            self.plot_tick_bottom.set_active(True)
        if config["plot_tick_top"]:
            self.plot_tick_top.set_active(True)
        if config["savefig_transparent"]:
            self.savefig_transparent_check_button.set_active(True)
        if config["plot_legend"]:
            self.plot_legend_check.set_active(True)
        if config["plot_invert_color_cycle_dark"]:
            self.plot_invert_color_cycle_dark.set_active(True)
        return config

    def get_font_weight(self, font_name):
        valid_weights = ['normal', 'bold', 'heavy', 'light', 'ultrabold', 'ultralight']
        if font_name[-2] != "italic":
            new_weight = font_name[-2]
        else:
            new_weight = font_name[-3]
        if new_weight not in valid_weights:
            new_weight = "normal"
        return new_weight

    def get_font_style(self, font_name):
        new_style = "normal"
        if font_name[-2] == ("italic" or "oblique" or "normal"):
            new_style = font_name[-2]
        return new_style


    def get_available_fonts(self):
        available_fonts = matplotlib.font_manager.get_font_names()
        font_list = []
        for font in available_fonts:
            font_list.append(font)
        return sorted(font_list)

    def set_config(self, parent):
        config = dict()
        font_name = self.plot_font_chooser.get_font_desc().to_string().lower().split(" ")
        font_size = font_name[-1]
        font_weight = self.get_font_weight(font_name)
        font_style = self.get_font_style(font_name)
        config["plot_font_string"] = self.plot_font_chooser.get_font_desc().to_string()
        config["plot_selected_marker_size"] = self.plot_selected_marker_size.get_value()
        config["plot_unselected_marker_size"] = self.plot_unselected_marker_size.get_value()
        config["selected_linewidth"] = self.selected_line_thickness_slider.get_value()
        config["unselected_linewidth"] = self.unselected_line_thickness_slider.get_value()
        config["plot_major_tick_width"] = self.plot_major_tick_width.get_value()
        config["plot_minor_tick_width"] = self.plot_minor_tick_width.get_value()
        config["plot_major_tick_length"] = self.plot_major_tick_length.get_value()
        config["plot_minor_tick_length"] = self.plot_minor_tick_length.get_value()
        config["savefig_transparent"] = self.savefig_transparent_check_button.get_active()
        config["plot_tick_left"] = self.plot_tick_left.get_active()
        config["plot_tick_right"] = self.plot_tick_right.get_active()
        config["plot_tick_top"] = self.plot_tick_top.get_active()
        config["plot_tick_bottom"] = self.plot_tick_bottom.get_active()
        config["plot_legend"] = self.plot_legend_check.get_active()
        config["plot_invert_color_cycle_dark"] = self.plot_invert_color_cycle_dark.get_active()
        config["plot_Y_label"] = self.plot_Y_label.get_text()
        config["plot_X_label"] = self.plot_X_label.get_text()
        config["plot_font_size"] = font_size
        config["plot_font_style"] = font_style
        config["plot_font_weight"] = font_weight
        config["plot_font_family"] = self.plot_font_chooser.get_font_desc().get_family()
        config["plot_title"] = self.plot_title.get_text()
        config["savefig_filetype"] = self.savefig_filetype_chooser.get_selected_item().get_string()
        config["plot_color_cycle"] = self.plot_color_cycle.get_selected_item().get_string()
        config["plot_X_scale"] = self.plot_X_scale.get_selected_item().get_string()
        config["plot_Y_scale"] = self.plot_Y_scale.get_selected_item().get_string()
        config["center_data"] = self.center_data_chooser.get_selected_item().get_string()
        config["plot_selected_linestyle"] = self.plot_selected_linestyle_chooser.get_selected_item().get_string()
        config["plot_tick_direction"] = self.plot_tick_direction.get_selected_item().get_string()
        config["plot_unselected_linestyle"] = self.plot_unselected_linestyle_chooser.get_selected_item().get_string()
        config["plot_style_dark"] = self.plot_style_dark.get_selected_item().get_string()
        config["plot_style_light"] = self.plot_style_light.get_selected_item().get_string()

        marker_dict = Line2D.markers
        unselected_marker_value = datman.get_dict_by_value(marker_dict, self.plot_unselected_markers_chooser.get_selected_item().get_string())
        selected_marker_value = datman.get_dict_by_value(marker_dict, self.plot_selected_markers_chooser.get_selected_item().get_string())
        config["plot_unselected_markers"] = unselected_marker_value
        config["plot_selected_markers"] = selected_marker_value
        return config

    def on_close(self, _, parent):
        parent.preferences.config = self.set_config(parent)
        parent.preferences.save_config()
        plotting_tools.reload_plot(parent)


