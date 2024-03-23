# SPDX-License-Identifier: GPL-3.0-or-later
"""
Module for importing data from files.

    Functions:
        import_from_files
"""
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, GObject, Gio, Graphs, Gtk

from graphs import parse_file, ui, utilities
from graphs.misc import ParseError


_IMPORT_MODES = {
    # name: suffix
    "project": ".graphs", "xrdml": ".xrdml", "xry": ".xry", "columns": None,
}


def import_from_files(
    application: Graphs.Application, files: list[Gio.File],
) -> None:
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
    settings = application.get_settings_child("import-params")
    for mode in settings.list_children():
        if mode in modes:
            configurable_modes.append(mode)
    if configurable_modes:
        _ImportDialog(application, settings, configurable_modes, import_dict)
    else:
        _import_from_files(
            application, settings, configurable_modes, import_dict,
        )


def _import_from_files(
    application: Graphs.Application, settings: Gio.Settings,
    configurable_modes: list[str], import_dict: dict,
):
    items = []
    style = application.get_figure_style_manager().get_selected_style_params()
    for mode, files in import_dict.items():
        callback = getattr(parse_file, "import_from_" + mode)
        params = settings.get_child(mode) if mode in configurable_modes \
            else None
        for file in files:
            try:
                items.extend(callback(params, style, file))
            except ParseError as error:
                application.get_window().add_toast_string(error.message)
                continue
    application.get_data().add_items(items)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/import.ui")
class _ImportDialog(Adw.Dialog):
    __gtype_name__ = "GraphsImportDialog"

    columns_group = Gtk.Template.Child()
    columns_delimiter = Gtk.Template.Child()
    columns_custom_delimiter = Gtk.Template.Child()
    columns_separator = Gtk.Template.Child()
    columns_column_x = Gtk.Template.Child()
    columns_column_y = Gtk.Template.Child()
    columns_skip_rows = Gtk.Template.Child()

    import_dict = GObject.Property(type=object)
    modes = GObject.Property(type=object)
    settings = GObject.Property(type=Gio.Settings)
    application = GObject.Property(type=Graphs.Application)

    def __init__(
        self, application: Graphs.Application, settings: Gio.Settings,
        modes: list[str], import_dict: dict,
    ):
        super().__init__(
            application=application,
            import_dict=import_dict, modes=modes, settings=settings,
        )

        for mode in modes:
            ui.bind_values_to_settings(
                settings.get_child(mode), self, prefix=f"{mode}_",
            )
            getattr(self, f"{mode}_group").set_visible(True)
        self.present(application.get_window())

    @Gtk.Template.Callback()
    def on_delimiter_change(self, _action, _target) -> None:
        delimiter_choice = self.columns_delimiter.get_selected()
        self.columns_custom_delimiter.set_visible(delimiter_choice == 6)

    @Gtk.Template.Callback()
    def on_reset(self, _widget) -> None:
        def on_accept(_dialog, response):
            if response == "reset":
                self.reset_import()
        body = _("Are you sure you want to reset the import settings?")
        dialog = ui.build_dialog("reset_to_defaults")
        dialog.set_body(body)
        dialog.connect("response", on_accept)
        dialog.present(self)

    def reset_import(self) -> None:
        for mode in self.props.modes:
            Graphs.tools_reset_settings(self.props.settings.get_child(mode))

    @Gtk.Template.Callback()
    def on_accept(self, _widget) -> None:
        _import_from_files(
            self.props.application, self.props.settings,
            self.props.modes, self.props.import_dict,
        )
        self.close()


def _guess_import_mode(file: Gio.File) -> str:
    try:
        filename = utilities.get_filename(file)
        file_suffix = Path(filename).suffixes[-1]
    except IndexError:
        file_suffix = None
    for mode, suffix in _IMPORT_MODES.items():
        if suffix is not None and file_suffix == suffix:
            return mode
    return "columns"
