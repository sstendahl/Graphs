# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, Gio, Gtk

from graphs import file_io, graphs, misc, plot_styles, utilities


class Preferences(dict):
    def __init__(self):
        self.load()

    def load(self):
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

        config = file_io.parse_json(config_file)
        config_template = file_io.parse_json(template_config_file)
        if set(config.keys()) != set(config_template.keys()):
            config = utilities.remove_unused_config_keys(
                config, config_template)
            config = utilities.add_new_config_keys(
                config, config_template)

        import_params = file_io.parse_json(import_file)
        import_params_template = file_io.parse_json(template_import_file)
        for key, item in import_params.items():
            if set(item.keys()) != set(import_params_template[key].keys()):
                import_params[key] = utilities.remove_unused_config_keys(
                    item, import_params_template[key])
                import_params[key] = utilities.add_new_config_keys(
                    item, import_params_template[key])
        if set(import_params.keys()) != set(import_params_template.keys()):
            import_params = utilities.remove_unused_config_keys(
                import_params, import_params_template)
            import_params = utilities.add_new_config_keys(
                import_params, import_params_template)

        config["import_params"] = import_params
        for key, item in config.items():
            self[key] = item

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

    def __init__(self, application):
        super().__init__(application=application)
        self.supported_filetypes = \
            self.props.application.canvas.get_supported_filetypes_grouped()

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
            self.plot_custom_style,
            plot_styles.get_user_styles(self.props.application).keys(),
            translate=False)
        self.load()
        self.set_transient_for(self.props.application.main_window)
        self.present()

    def load(self):
        preferences = self.props.application.preferences
        self.clipboard_length.set_value(int(preferences["clipboard_length"]))

        columns_params = preferences["import_params"]["columns"]
        self.import_delimiter.set_text(columns_params["delimiter"])
        utilities.set_chooser(
            self.import_separator, columns_params["separator"])
        self.import_column_x.set_value(columns_params["column_x"])
        self.import_column_y.set_value(columns_params["column_y"])
        self.import_skip_rows.set_value(columns_params["skip_rows"])
        self.addequation_equation.set_text(preferences["addequation_equation"])
        self.addequation_x_start.set_text(preferences["addequation_x_start"])
        self.addequation_x_stop.set_text(preferences["addequation_x_stop"])
        self.addequation_step_size.set_text(
            preferences["addequation_step_size"])
        self.export_figure_dpi.set_value(int(preferences["export_figure_dpi"]))
        for name, formats in self.supported_filetypes.items():
            if preferences["export_figure_filetype"] in formats:
                filetype = name
        utilities.set_chooser(self.export_figure_filetype, filetype)
        self.export_figure_transparent.set_active(
            preferences["export_figure_transparent"])
        utilities.set_chooser(
            self.action_center_data, preferences["action_center_data"])
        utilities.set_chooser(
            self.other_handle_duplicates, preferences["handle_duplicates"])
        self.other_hide_unselected.set_active(preferences["hide_unselected"])
        self.override_style_change.set_active(
            preferences["override_style_change"])
        self.plot_title.set_text(preferences["plot_title"])
        self.plot_x_label.set_text(preferences["plot_x_label"])
        self.plot_y_label.set_text(preferences["plot_y_label"])
        self.plot_top_label.set_text(preferences["plot_top_label"])
        self.plot_right_label.set_text(preferences["plot_right_label"])
        utilities.set_chooser(
            self.plot_x_scale, preferences["plot_x_scale"])
        utilities.set_chooser(
            self.plot_y_scale, preferences["plot_y_scale"])
        utilities.set_chooser(
            self.plot_top_scale, preferences["plot_top_scale"])
        utilities.set_chooser(
            self.plot_right_scale, preferences["plot_right_scale"])
        utilities.set_chooser(
            self.plot_x_position, preferences["plot_x_position"])
        utilities.set_chooser(
            self.plot_y_position, preferences["plot_y_position"])
        utilities.set_chooser(
            self.plot_legend_position,
            preferences["plot_legend_position"].capitalize())
        self.plot_legend.set_enable_expansion(preferences["plot_legend"])
        self.plot_use_custom_style.set_enable_expansion(
            preferences["plot_use_custom_style"])
        utilities.set_chooser(
            self.plot_custom_style, preferences["plot_custom_style"])

    def apply(self):
        preferences = self.props.application.preferences
        columns_params = preferences["import_params"]["columns"]
        columns_params["delimiter"] = self.import_delimiter.get_text()
        columns_params["separator"] = \
            utilities.get_selected_chooser_item(self.import_separator)
        columns_params["column_x"] = int(self.import_column_x.get_value())
        columns_params["column_y"] = int(self.import_column_y.get_value())
        columns_params["skip_rows"] = int(self.import_skip_rows.get_value())
        preferences["addequation_equation"] = \
            self.addequation_equation.get_text()
        preferences["addequation_x_start"] = \
            self.addequation_x_start.get_text()
        preferences["addequation_x_stop"] = \
            self.addequation_x_stop.get_text()
        preferences["addequation_step_size"] = \
            self.addequation_step_size.get_text()
        preferences["clipboard_length"] = self.clipboard_length.get_value()
        preferences["export_figure_dpi"] = self.export_figure_dpi.get_value()
        filetype_name = \
            utilities.get_selected_chooser_item(self.export_figure_filetype)
        filetypes = \
            self.props.application.canvas.get_supported_filetypes_grouped()
        for name, formats in filetypes.items():
            if name == filetype_name:
                export_figure_filetyope = formats[0]
        preferences["export_figure_filetype"] = export_figure_filetyope
        preferences["export_figure_transparent"] = \
            self.export_figure_transparent.get_active()
        preferences["action_center_data"] = \
            utilities.get_selected_chooser_item(self.action_center_data)
        preferences["handle_duplicates"] = \
            utilities.get_selected_chooser_item(self.other_handle_duplicates)
        preferences["hide_unselected"] = \
            self.other_hide_unselected.get_active()
        preferences["override_style_change"] = \
            self.override_style_change.get_active()
        preferences["plot_title"] = self.plot_title.get_text()
        preferences["plot_x_label"] = self.plot_x_label.get_text()
        preferences["plot_y_label"] = self.plot_y_label.get_text()
        preferences["plot_top_label"] = self.plot_top_label.get_text()
        preferences["plot_right_label"] = self.plot_right_label.get_text()
        preferences["plot_x_scale"] = \
            utilities.get_selected_chooser_item(self.plot_x_scale)
        preferences["plot_y_scale"] = \
            utilities.get_selected_chooser_item(self.plot_y_scale)
        preferences["plot_top_scale"] = \
            utilities.get_selected_chooser_item(self.plot_top_scale)
        preferences["plot_right_scale"] = \
            utilities.get_selected_chooser_item(self.plot_right_scale)
        preferences["plot_x_position"] = \
            utilities.get_selected_chooser_item(self.plot_x_position)
        preferences["plot_y_position"] = \
            utilities.get_selected_chooser_item(self.plot_y_position)
        preferences["plot_legend"] = self.plot_legend.get_enable_expansion()
        preferences["plot_legend_position"] = \
            utilities.get_selected_chooser_item(
                self.plot_legend_position).lower()
        preferences["plot_use_custom_style"] = \
            self.plot_use_custom_style.get_enable_expansion()
        preferences["plot_custom_style"] = \
            utilities.get_selected_chooser_item(self.plot_custom_style)

    @Gtk.Template.Callback()
    def on_close(self, _):
        self.apply()
        self.props.application.preferences.save()
        graphs.refresh(self.props.application)
