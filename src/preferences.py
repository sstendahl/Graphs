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

        self.update(_validate(
            file_io.parse_json(config_file),
            file_io.parse_json(template_config_file)))

        import_params_template = file_io.parse_json(template_import_file)
        self["import_params"] = _validate({
            key: _validate(item, import_params_template[key])
            for key, item in file_io.parse_json(import_file).items()
        }, import_params_template)

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


CONFIG_IGNORELIST = [
    "import_params", "export_figure_filetype",
]


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
        ui.load_values_from_dict(self, self.props.application.preferences,
                                 ignorelist=CONFIG_IGNORELIST)
        columns_params = \
            self.props.application.preferences["import_params"]["columns"]
        self.import_delimiter.set_text(columns_params["delimiter"])
        utilities.set_chooser(
            self.import_separator, columns_params["separator"])
        self.import_column_x.set_value(columns_params["column_x"])
        self.import_column_y.set_value(columns_params["column_y"])
        self.import_skip_rows.set_value(columns_params["skip_rows"])

        wanted_filetype = \
            self.props.application.preferences["export_figure_filetype"]
        for name, formats in self.supported_filetypes.items():
            if wanted_filetype in formats:
                filetype = name
        utilities.set_chooser(self.export_figure_filetype, filetype)

    def apply(self):
        ui.save_values_to_dict(self, self.props.application.preferences,
                               ignorelist=CONFIG_IGNORELIST)
        columns_params = \
            self.props.application.preferences["import_params"]["columns"]
        columns_params["delimiter"] = self.import_delimiter.get_text()
        columns_params["separator"] = \
            utilities.get_selected_chooser_item(self.import_separator)
        columns_params["column_x"] = int(self.import_column_x.get_value())
        columns_params["column_y"] = int(self.import_column_y.get_value())
        columns_params["skip_rows"] = int(self.import_skip_rows.get_value())

        filetype_name = \
            utilities.get_selected_chooser_item(self.export_figure_filetype)
        filetypes = \
            self.props.application.canvas.get_supported_filetypes_grouped()
        for name, formats in filetypes.items():
            if name == filetype_name:
                export_figure_filetype = formats[0]
        self.props.application.preferences["export_figure_filetype"] = \
            export_figure_filetype

    @Gtk.Template.Callback()
    def on_close(self, _):
        self.apply()
        self.props.application.preferences.save()
        graphs.refresh(self.props.application)
