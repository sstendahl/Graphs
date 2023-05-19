# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, Gio, Gtk

from graphs import file_io, graphs, misc, plot_styles, utilities


class Preferences():
    def __init__(self, parent):
        self.parent = parent
        self.template_file = Gio.File.new_for_uri(
            "resource:///se/sjoerd/Graphs/config.json")
        self.check_config()
        self.config = self.load_config()

    def check_config(self):
        config_dir = utilities.get_config_directory()
        if not config_dir.query_exists(None):
            config_dir.make_directory_with_parents(None)
        self.config_file = config_dir.get_child_for_display_name("config.json")
        if not self.config_file.query_exists(None):
            self.template_file.copy(
                self.config_file, Gio.FileCopyFlags(1), None, None, None)
            logging.info(_("New configuration file created"))

    def load_config(self):
        logging.debug(_("Loading configuration file"))
        config = file_io.parse_json(self.config_file)
        template = file_io.parse_json(self.template_file)
        if set(config.keys()) != set(template.keys()):
            config = utilities.remove_unused_config_keys(config, template)
            config = utilities.add_new_config_keys(config, template)
        return config

    def save_config(self):
        file_io.write_json(self.config_file, self.config)


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
        self.supported_filetypes = \
            self.parent.canvas.get_supported_filetypes_grouped()

        utilities.populate_chooser(
            self.import_separator, misc.SEPARATORS, translate=False)
        utilities.populate_chooser(
            self.export_figure_filetype, self.supported_filetypes.keys(),
            translate=False)
        utilities.populate_chooser(
            self.action_center_data, misc.ACTION_CENTER_DATA)
        utilities.populate_chooser(
            self.other_handle_duplicates, misc.HANDLE_DUPLICATES)
        utilities.populate_chooser(self.plot_x_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_y_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_top_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_right_scale, misc.SCALES)
        utilities.populate_chooser(self.plot_x_position, misc.X_POSITIONS)
        utilities.populate_chooser(self.plot_y_position, misc.Y_POSITIONS)
        utilities.populate_chooser(
            self.plot_legend_position, misc.LEGEND_POSITIONS)

        utilities.populate_chooser(
            self.plot_custom_style, plot_styles.get_user_styles(parent).keys(),
            translate=False)
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
        for name, formats in self.supported_filetypes.items():
            if config["export_figure_filetype"] in formats:
                filetype = name
        utilities.set_chooser(self.export_figure_filetype, filetype)
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
            utilities.get_selected_chooser_item(self.import_separator)
        config["import_column_x"] = int(self.import_column_x.get_value())
        config["import_column_y"] = int(self.import_column_y.get_value())
        config["import_skip_rows"] = int(self.import_skip_rows.get_value())
        config["addequation_equation"] = self.addequation_equation.get_text()
        config["addequation_x_start"] = self.addequation_x_start.get_text()
        config["addequation_x_stop"] = self.addequation_x_stop.get_text()
        config["addequation_step_size"] = self.addequation_step_size.get_text()
        config["clipboard_length"] = int(self.clipboard_length.get_value())
        config["export_figure_dpi"] = int(self.export_figure_dpi.get_value())
        filetype_name = \
            utilities.get_selected_chooser_item(self.export_figure_filetype)
        for name, formats in \
                self.parent.canvas.get_supported_filetypes_grouped().items():
            if name == filetype_name:
                export_figure_filetyope = formats[0]
        config["export_figure_filetype"] = export_figure_filetyope
        config["export_figure_transparent"] = \
            self.export_figure_transparent.get_active()
        config["action_center_data"] = \
            utilities.get_selected_chooser_item(self.action_center_data)
        config["handle_duplicates"] = \
            utilities.get_selected_chooser_item(self.other_handle_duplicates)
        config["hide_unselected"] = self.other_hide_unselected.get_active()
        config["override_style_change"] = \
            self.override_style_change.get_active()
        config["plot_title"] = self.plot_title.get_text()
        config["plot_x_label"] = self.plot_x_label.get_text()
        config["plot_y_label"] = self.plot_y_label.get_text()
        config["plot_top_label"] = self.plot_top_label.get_text()
        config["plot_right_label"] = self.plot_right_label.get_text()
        config["plot_x_scale"] = \
            utilities.get_selected_chooser_item(self.plot_x_scale)
        config["plot_y_scale"] = \
            utilities.get_selected_chooser_item(self.plot_y_scale)
        config["plot_top_scale"] = \
            utilities.get_selected_chooser_item(self.plot_top_scale)
        config["plot_right_scale"] = \
            utilities.get_selected_chooser_item(self.plot_right_scale)
        config["plot_x_position"] = \
            utilities.get_selected_chooser_item(self.plot_x_position)
        config["plot_y_position"] = \
            utilities.get_selected_chooser_item(self.plot_y_position)
        config["plot_legend"] = self.plot_legend.get_enable_expansion()
        config["plot_legend_position"] = \
            utilities.get_selected_chooser_item(
                self.plot_legend_position).lower()
        config["plot_use_custom_style"] = \
            self.plot_use_custom_style.get_enable_expansion()
        config["plot_custom_style"] = \
            utilities.get_selected_chooser_item(self.plot_custom_style)

    def on_close(self, _, parent):
        self.apply_configuration()
        parent.preferences.save_config()
        graphs.reload(parent)
