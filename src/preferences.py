# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
import shutil

from gi.repository import Adw, Gtk

from graphs import utilities

import matplotlib.font_manager
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


class Preferences():
    def __init__(self, parent):
        self.parent = parent
        self.create_new_config_file()
        self.config = self.load_config()
        self.check_config(self.config)

    def check_config(self, config):
        template_path = os.path.join(os.getenv('XDG_DATA_DIRS'))
        template_path = template_path.split(':')[0] + '/graphs/graphs'
        os.chdir(template_path)
        with open('config.json', 'r') as file:
            template = json.load(file)
        if set(config.keys()) != set(template.keys()):
            config = utilities.remove_unused_config_keys(config, template)
            config = utilities.add_new_config_keys(config, template)
        return config

    def create_new_config_file(self):
        config_path = self.get_config_path()
        if not os.path.isfile(f'{config_path}/config.json'):
            self.reset_config()
            print('New configuration file created')
        else:
            print('Loading configuration file')

    def reset_config(self):
        config_path = self.get_config_path()
        old_path = os.path.join(os.getenv('XDG_DATA_DIRS'))
        old_path = old_path.split(':')[0] + '/graphs/graphs'
        if not os.path.isdir(config_path):
            os.mkdir(config_path)
        path = config_path + '/config.json'
        shutil.copy(f'{old_path}/config.json', path)
        print('Loaded new config')

    def load_config(self):
        config_path = self.get_config_path()
        os.chdir(config_path)
        with open('config.json', 'r') as file:
            config = json.load(file)
        config = self.check_config(config)
        return config

    def save_config(self):
        config_path = self.get_config_path()
        os.chdir(config_path)
        with open('config.json', 'w') as file:
            json.dump(self.config, file)

    def get_config_path(self) -> str:
        if os.getenv('XDG_CONFIG_HOME'):
            return os.path.join(os.getenv('XDG_CONFIG_HOME'), 'Graphs')
        else:
            return os.path.join(str(Path.home()), '.local', 'share', 'Graphs')


@Gtk.Template(resource_path='/se/sjoerd/Graphs/ui/preferences.ui')
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'PreferencesWindow'
    selected_line_thickness_slider = Gtk.Template.Child()
    unselected_line_thickness_slider = Gtk.Template.Child()
    savefig_transparent_check_button = Gtk.Template.Child()
    savefig_filetype_chooser = Gtk.Template.Child()
    savefig_filetype_list = Gtk.Template.Child()
    addequation_equation = Gtk.Template.Child()
    addequation_X_start = Gtk.Template.Child()
    addequation_X_stop = Gtk.Template.Child()
    addequation_step_size = Gtk.Template.Child()
    plot_Y_label = Gtk.Template.Child()
    plot_X_label = Gtk.Template.Child()
    plot_right_label = Gtk.Template.Child()
    plot_top_label = Gtk.Template.Child()
    plot_Y_position = Gtk.Template.Child()
    plot_X_position = Gtk.Template.Child()
    plot_X_scale = Gtk.Template.Child()
    plot_Y_scale = Gtk.Template.Child()
    plot_top_scale = Gtk.Template.Child()
    plot_right_scale = Gtk.Template.Child()
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
    handle_duplicates_chooser = Gtk.Template.Child()
    column_x = Gtk.Template.Child()
    column_y = Gtk.Template.Child()
    import_skip_rows = Gtk.Template.Child()
    import_separator = Gtk.Template.Child()
    import_delimiter = Gtk.Template.Child()
    guess_headers = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.props.modal = True
        color_cycles = [
            'Pastel1', 'Pastel2', 'Paired', 'Accent',
            'Dark2', 'Set1', 'Set2', 'Set3',
            'tab10', 'tab20', 'tab20b', 'tab20c']
        utilities.populate_chooser(self.plot_color_cycle, color_cycles)
        utilities.populate_chooser(self.plot_style_dark, plt.style.available)
        utilities.populate_chooser(self.plot_style_light, plt.style.available)
        utilities.populate_chooser(self.plot_selected_markers_chooser, list(Line2D.markers.values()), clear=False)
        utilities.populate_chooser(self.plot_unselected_markers_chooser, list(Line2D.markers.values()), clear=False)
        config = parent.preferences.config
        config = self.load_configuration(config)
        self.connect('close-request', self.on_close, parent)
        self.set_transient_for(parent.main_window)

    def load_configuration(self, config):
        font_string = config['plot_font_string']
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
        self.addequation_equation.set_text(str(config['addequation_equation']))
        self.addequation_X_start.set_text(str(config['addequation_X_start']))
        self.addequation_X_stop.set_text(str(config['addequation_X_stop']))
        self.addequation_step_size.set_text(str(config['addequation_step_size']))
        self.import_skip_rows.set_value(int(config['import_skip_rows']))
        self.column_y.set_value(int(config['import_column_y']))
        self.column_x.set_value(int(config['import_column_x']))
        self.import_delimiter.set_text(config['import_delimiter'])
        self.plot_selected_marker_size.set_value(config['plot_selected_marker_size'])
        self.plot_unselected_marker_size.set_value(config['plot_unselected_marker_size'])
        self.unselected_line_thickness_slider.set_value(config['unselected_linewidth'])
        self.selected_line_thickness_slider.set_value(config['selected_linewidth'])
        self.plot_minor_tick_width.set_value(config['plot_minor_tick_width'])
        self.plot_major_tick_width.set_value(config['plot_major_tick_width'])
        self.plot_minor_tick_length.set_value(config['plot_minor_tick_length'])
        self.plot_major_tick_length.set_value(config['plot_major_tick_length'])
        self.plot_Y_label.set_text(config['plot_Y_label'])
        self.plot_X_label.set_text(config['plot_X_label'])
        self.plot_right_label.set_text(config['plot_right_label'])
        self.plot_top_label.set_text(config['plot_top_label'])
        self.plot_title.set_text(config['plot_title'])
        utilities.set_chooser(self.savefig_filetype_chooser, config['savefig_filetype'])
        utilities.set_chooser(self.center_data_chooser, config['action_center_data'])
        utilities.set_chooser(self.plot_X_scale, config['plot_X_scale'])
        utilities.set_chooser(self.plot_top_scale, config['plot_top_scale'])
        utilities.set_chooser(self.plot_right_scale, config['plot_right_scale'])
        utilities.set_chooser(self.plot_Y_scale, config['plot_Y_scale'])
        utilities.set_chooser(self.plot_X_position, config['plot_X_position'])
        utilities.set_chooser(self.plot_Y_position, config['plot_Y_position'])
        utilities.set_chooser(self.plot_tick_direction, config['plot_tick_direction'])
        utilities.set_chooser(self.handle_duplicates_chooser, config['handle_duplicates'])
        utilities.set_chooser(self.import_separator, config['import_separator'])
        utilities.set_chooser(self.plot_color_cycle, config['plot_color_cycle'])
        utilities.set_chooser(self.plot_selected_linestyle_chooser, config['plot_selected_linestyle'])
        utilities.set_chooser(self.plot_unselected_linestyle_chooser, config['plot_unselected_linestyle'])
        utilities.set_chooser(self.plot_style_light, config['plot_style_light'])
        utilities.set_chooser(self.plot_style_dark, config['plot_style_dark'])
        marker_dict = Line2D.markers
        unselected_marker_value = marker_dict[config['plot_unselected_markers']]
        selected_marker_value = marker_dict[config['plot_selected_markers']]
        utilities.set_chooser(self.plot_selected_markers_chooser, selected_marker_value)
        utilities.set_chooser(self.plot_unselected_markers_chooser, unselected_marker_value)
        if config['plot_tick_left']:
            self.plot_tick_left.set_active(True)
        if config['plot_tick_right']:
            self.plot_tick_right.set_active(True)
        if config['plot_tick_bottom']:
            self.plot_tick_bottom.set_active(True)
        if config['plot_tick_top']:
            self.plot_tick_top.set_active(True)
        if config['guess_headers']:
            self.guess_headers.set_active(True)
        if config['savefig_transparent']:
            self.savefig_transparent_check_button.set_active(True)
        if config['plot_legend']:
            self.plot_legend_check.set_active(True)
        if config['plot_invert_color_cycle_dark']:
            self.plot_invert_color_cycle_dark.set_active(True)
        return config

    def get_font_weight(self, font_name):
        valid_weights = ['normal', 'bold', 'heavy', 'light', 'ultrabold', 'ultralight']
        if font_name[-2] != 'italic':
            new_weight = font_name[-2]
        else:
            new_weight = font_name[-3]
        if new_weight not in valid_weights:
            new_weight = 'normal'
        return new_weight

    def get_font_style(self, font_name):
        new_style = 'normal'
        if font_name[-2] == ('italic' or 'oblique' or 'normal'):
            new_style = font_name[-2]
        return new_style

    def get_available_fonts(self):
        available_fonts = matplotlib.font_manager.get_font_names()
        font_list = []
        for font in available_fonts:
            font_list.append(font)
        return sorted(font_list)

    def set_config(self):
        config = {}
        font_name = self.plot_font_chooser.get_font_desc().to_string().lower().split(' ')
        font_size = font_name[-1]
        font_weight = self.get_font_weight(font_name)
        font_style = self.get_font_style(font_name)
        config['addequation_equation'] = self.addequation_equation.get_text()
        config['addequation_X_start'] = self.addequation_X_start.get_text()
        config['addequation_X_stop'] = self.addequation_X_stop.get_text()
        config['addequation_step_size'] = self.addequation_step_size.get_text()
        config['plot_font_string'] = self.plot_font_chooser.get_font_desc().to_string()
        config['plot_selected_marker_size'] = self.plot_selected_marker_size.get_value()
        config['plot_unselected_marker_size'] = self.plot_unselected_marker_size.get_value()
        config['selected_linewidth'] = self.selected_line_thickness_slider.get_value()
        config['unselected_linewidth'] = self.unselected_line_thickness_slider.get_value()
        config['plot_major_tick_width'] = self.plot_major_tick_width.get_value()
        config['plot_minor_tick_width'] = self.plot_minor_tick_width.get_value()
        config['plot_major_tick_length'] = self.plot_major_tick_length.get_value()
        config['plot_minor_tick_length'] = self.plot_minor_tick_length.get_value()
        config['plot_tick_left'] = self.plot_tick_left.get_active()
        config['plot_tick_right'] = self.plot_tick_right.get_active()
        config['plot_tick_top'] = self.plot_tick_top.get_active()
        config['plot_tick_bottom'] = self.plot_tick_bottom.get_active()
        config['plot_tick_direction'] = self.plot_tick_direction.get_selected_item().get_string()
        config['guess_headers'] = self.guess_headers.get_active()
        config['handle_duplicates'] = self.handle_duplicates_chooser.get_selected_item().get_string()
        config['savefig_transparent'] = self.savefig_transparent_check_button.get_active()
        config['plot_legend'] = self.plot_legend_check.get_active()
        config['plot_invert_color_cycle_dark'] = self.plot_invert_color_cycle_dark.get_active()
        config['plot_Y_label'] = self.plot_Y_label.get_text()
        config['plot_X_label'] = self.plot_X_label.get_text()
        config['plot_right_label'] = self.plot_right_label.get_text()
        config['plot_top_label'] = self.plot_top_label.get_text()
        config['plot_font_size'] = font_size
        config['plot_font_style'] = font_style
        config['plot_font_weight'] = font_weight
        config['plot_font_family'] = self.plot_font_chooser.get_font_desc().get_family()
        config['plot_title'] = self.plot_title.get_text()
        config['savefig_filetype'] = self.savefig_filetype_chooser.get_selected_item().get_string()
        config['plot_color_cycle'] = self.plot_color_cycle.get_selected_item().get_string()
        config['plot_X_scale'] = self.plot_X_scale.get_selected_item().get_string()
        config['plot_Y_scale'] = self.plot_Y_scale.get_selected_item().get_string()
        config['plot_top_scale'] = self.plot_top_scale.get_selected_item().get_string()
        config['plot_right_scale'] = self.plot_right_scale.get_selected_item().get_string()
        config['plot_right_scale'] = self.plot_right_scale.get_selected_item().get_string()
        config['plot_top_scale'] = self.plot_top_scale.get_selected_item().get_string()
        config['plot_X_position'] = self.plot_X_position.get_selected_item().get_string()
        config['plot_Y_position'] = self.plot_Y_position.get_selected_item().get_string()
        config['action_center_data'] = self.center_data_chooser.get_selected_item().get_string()
        config['plot_selected_linestyle'] = self.plot_selected_linestyle_chooser.get_selected_item().get_string()
        config['plot_unselected_linestyle'] = self.plot_unselected_linestyle_chooser.get_selected_item().get_string()
        config['plot_style_dark'] = self.plot_style_dark.get_selected_item().get_string()
        config['plot_style_light'] = self.plot_style_light.get_selected_item().get_string()
        config['import_column_x'] = int(self.column_x.get_value())
        config['import_column_y'] = int(self.column_y.get_value())
        config['import_skip_rows'] = int(self.import_skip_rows.get_value())
        config['import_separator'] = self.import_separator.get_selected_item().get_string()
        config['import_delimiter'] = self.import_delimiter.get_text()
        marker_dict = Line2D.markers
        unselected_marker_value = utilities.get_dict_by_value(marker_dict, self.plot_unselected_markers_chooser.get_selected_item().get_string())
        selected_marker_value = utilities.get_dict_by_value(marker_dict, self.plot_selected_markers_chooser.get_selected_item().get_string())
        config['plot_unselected_markers'] = unselected_marker_value
        config['plot_selected_markers'] = selected_marker_value
        return config

    def on_close(self, _, parent):
        parent.preferences.config = self.set_config()
        parent.preferences.save_config()
