# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path

from gi.repository import Adw, GObject, Gtk

from graphs import file_io, graphs, misc, ui, utilities
from graphs.misc import ParseError


IMPORT_MODES = ["project", "xrdml", "xry", "columns"]


def prepare_import(self, files):
    import_dict = {mode: [] for mode in IMPORT_MODES}
    for file in files:
        import_dict[guess_import_mode(file)].append(file)
    modes = []
    for mode, files in import_dict.items():
        if files:
            modes.append(mode)
    if modes:
        ImportWindow(self, modes, import_dict)
        return
    prepare_import_finish(self, import_dict)


def prepare_import_finish(self, import_dict):
    import_settings_list = []
    for mode, files in import_dict.items():
        try:
            params = self.preferences["import_params"][mode]
        except KeyError:
            params = []
        for file in files:
            import_settings_list.append(ImportSettings(file, mode, params))
    import_from_files(self, import_settings_list)


def import_from_files(self, import_settings_list):
    items = []
    for import_settings in import_settings_list:
        try:
            items.extend(_import_from_file(self, import_settings))
        except ParseError as error:
            self.main_window.add_toast(error.message)
            continue
    graphs.add_items(self, items)


def _import_from_file(self, import_settings):
    match import_settings.mode:
        case "project":
            callback = file_io.import_from_project
        case "xrdml":
            callback = file_io.import_from_xrdml
        case "xry":
            callback = file_io.import_from_xry
        case "columns":
            callback = file_io.import_from_columns
    return callback(self, import_settings)


class ImportSettings():
    def __init__(self, file, mode, params):
        self.file = file
        self.mode = mode
        self.params = params
        self.name = file.query_info("standard::*", 0, None).get_display_name()


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/import.ui")
class ImportWindow(Adw.Window):
    __gtype_name__ = "ImportWindow"

    columns_group = Gtk.Template.Child()
    columns_delimiter = Gtk.Template.Child()
    columns_separator = Gtk.Template.Child()
    columns_column_x = Gtk.Template.Child()
    columns_column_y = Gtk.Template.Child()
    columns_skip_rows = Gtk.Template.Child()

    modes = GObject.Property(type=object)
    import_dict = GObject.Property(type=object)

    def __init__(self, application, modes, import_dict):
        super().__init__(
            application=application, transient_for=application.main_window,
            modes=modes, import_dict=import_dict,
        )

        utilities.populate_chooser(
            self.columns_separator, misc.SEPARATORS, False)

        visible = False
        for mode, values \
                in self.props.application.preferences["import_params"].items():
            if mode in self.modes:
                ui.load_values_from_dict(self, {
                    f"{mode}_{key}": value for key, value in values.items()})
                getattr(self, f"{mode}_group").set_visible(True)
                visible = True

        if not visible:
            prepare_import_finish(self.props.application, self.import_dict)
            self.destroy()
            return
        self.present()

    @Gtk.Template.Callback()
    def on_accept(self, _widget):
        save_values = True

        param_dict = {
            mode: {
                key.replace(f"{mode}_", ""): value for key, value
                in ui.save_values_to_dict(
                    self, [f"{mode}_{key}" for key in params.keys()],
                ).items()
            } for mode, params
            in self.props.application.preferences["import_params"].items()
            if mode in self.modes
        }

        if save_values:
            self.props.application.preferences.update_modes(param_dict)

        import_from_files(self.props.application, [
            ImportSettings(
                file, mode, param_dict[mode] if mode in self.modes else [])
            for mode in IMPORT_MODES for file in self.import_dict[mode]
        ])
        self.destroy()


def guess_import_mode(file):
    try:
        filename = file.query_info("standard::*", 0, None).get_display_name()
        file_suffix = Path(filename).suffixes[-1]
    except IndexError:
        file_suffix = None
    match file_suffix:
        case ".graphs":
            return "project"
        case ".xrdml":
            return "xrdml"
        case ".xry":
            return "xry"
        case _:
            return "columns"
