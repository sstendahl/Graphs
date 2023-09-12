# SPDX-License-Identifier: GPL-3.0-or-later
"""
Module for importing data from files.

    Functions:
        import_from_files
"""
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, GObject, Gtk

from graphs import parse_file, ui, utilities
from graphs.misc import ParseError


_IMPORT_MODES = {
    # name: suffix
    "project": ".graphs", "xrdml": ".xrdml", "xry": ".xry", "columns": None,
}


def import_from_files(self, files: list):
    """
    Import from a list of files.

    Automatically guesses, which mode to use. If configurable settings are
    present at /se/sjoerd/Graphs/import-params, a Window will be shown,
    giving the option to configure them.
    """
    import_dict = {mode: [] for mode in _IMPORT_MODES.keys()}
    for file in files:
        import_dict[_guess_import_mode(file)].append(file)
    modes = []
    for mode, files in import_dict.items():
        if files:
            modes.append(mode)
    configurable_modes = []
    for mode in self.get_settings("import-params").list_children():
        if mode in modes:
            configurable_modes.append(mode)
    if configurable_modes:
        _ImportWindow(self, configurable_modes, import_dict)
    else:
        _import_from_files(self, import_dict)


def _import_from_files(self, import_dict: dict):
    items = []
    for mode, files in import_dict.items():
        callback = getattr(parse_file, "import_from_" + mode)
        for file in files:
            try:
                items.extend(callback(self, file))
            except ParseError as error:
                self.get_window().add_toast_string(error.message)
                continue
    self.get_data().add_items(items)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/import.ui")
class _ImportWindow(Adw.Window):
    __gtype_name__ = "ImportWindow"

    columns_group = Gtk.Template.Child()
    columns_delimiter = Gtk.Template.Child()
    columns_separator = Gtk.Template.Child()
    columns_column_x = Gtk.Template.Child()
    columns_column_y = Gtk.Template.Child()
    columns_skip_rows = Gtk.Template.Child()

    import_dict = GObject.Property(type=object)

    def __init__(self, application, modes: list, import_dict: dict):
        super().__init__(
            application=application, transient_for=application.get_window(),
            import_dict=import_dict,
        )

        import_params = \
            self.get_application().get_settings("import-params")
        for mode in modes:
            ui.bind_values_to_settings(
                import_params.get_child(mode), self, prefix=f"{mode}_",
            )
            getattr(self, f"{mode}_group").set_visible(True)
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
            self.get_application().get_settings("import-params")
        for mode in import_params.list_children():
            settings = import_params.get_child(mode)
            for key in settings.props.settings_schema.list_keys():
                settings.reset(key)

    @Gtk.Template.Callback()
    def on_accept(self, _widget):
        _import_from_files(self.get_application(), self.import_dict)
        self.destroy()


def _guess_import_mode(file):
    try:
        filename = utilities.get_filename(file)
        file_suffix = Path(filename).suffixes[-1]
    except IndexError:
        file_suffix = None
    for mode, suffix in _IMPORT_MODES.items():
        if suffix is not None and file_suffix == suffix:
            return mode
    return "columns"
