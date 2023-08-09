# SPDX-License-Identifier: GPL-3.0-or-later
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, GObject, Gio, Gtk

from graphs import file_io, graphs, ui, utilities
from graphs.misc import ParseError


IMPORT_MODES = {
    # name: suffix
    "project": ".graphs", "xrdml": ".xrdml", "xry": ".xry", "columns": None,
}


class ImportSettings(GObject.Object):
    file = GObject.Property(type=Gio.File)
    mode = GObject.Property(type=str, default="columns")
    name = GObject.Property(type=str, default=_("Imported Data"))


def prepare_import(self, files: list):
    import_dict = {mode: [] for mode in IMPORT_MODES.keys()}
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


def prepare_import_finish(self, import_dict: dict):
    import_from_files(self, [
        ImportSettings(file=file, mode=mode, name=utilities.get_filename(file))
        for mode, files in import_dict.items() for file in files
    ])


def import_from_files(self, import_settings_list: list):
    items = []
    for import_settings in import_settings_list:
        try:
            items.extend(_import_from_file(self, import_settings))
        except ParseError as error:
            self.main_window.add_toast(error.message)
            continue
    graphs.add_items(self, items)


def _import_from_file(self, import_settings: ImportSettings):
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

    def __init__(self, application, modes: list, import_dict: dict):
        super().__init__(
            application=application, transient_for=application.main_window,
            modes=modes, import_dict=import_dict,
        )

        import_params = \
            self.props.application.settings.get_child("import-params")
        visible = False
        for mode in import_params.list_children():
            if mode in self.modes:
                ui.bind_values_to_settings(
                    import_params.get_child(mode), self, prefix=f"{mode}_")
                getattr(self, f"{mode}_group").set_visible(True)
                visible = True

        if not visible:
            prepare_import_finish(self.props.application, self.import_dict)
            self.destroy()
            return
        self.present()

    @Gtk.Template.Callback()
    def on_reset(self, _widget):
        def on_accept(_dialog, response):
            if response == "reset":
                self.reset_import()
        body = _("Are you sure you want to reset the import settings?")
        dialog = ui.build_dialog("reset_to_defaults")
        dialog.set_body(body)
        dialog.set_transient_for(self)
        dialog.connect("response", on_accept)
        dialog.present()

    def reset_import(self):
        import_params = \
            self.props.application.settings.get_child("import-params")
        for mode in import_params.list_children():
            settings = import_params.get_child(mode)
            for key in settings.props.settings_schema.list_keys():
                settings.reset(key)

    @Gtk.Template.Callback()
    def on_accept(self, _widget):
        import_from_files(self.props.application, [
            ImportSettings(
                file=file, mode=mode, name=utilities.get_filename(file))
            for mode in IMPORT_MODES.keys() for file in self.import_dict[mode]
        ])
        self.destroy()


def guess_import_mode(file):
    try:
        filename = utilities.get_filename(file)
        file_suffix = Path(filename).suffixes[-1]
    except IndexError:
        file_suffix = None
    for mode, suffix in IMPORT_MODES.items():
        if suffix is not None and file_suffix == suffix:
            return mode
    return "columns"
