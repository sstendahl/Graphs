# SPDX-License-Identifier: GPL-3.0-or-later
"""
Module for importing data from files.

    Functions:
        import_from_files
"""
from pathlib import Path

from gi.repository import Gio, Graphs

from graphs import parse_file
from graphs.misc import ParseError

_IMPORT_MODES = {
    # name: suffix
    "project": ".graphs",
    "xrdml": ".xrdml",
    "xry": ".xry",
    "columns": None,
}


def import_from_files(
    window: Graphs.Window,
    files: list[Gio.File],
) -> None:
    """
    Import from a list of files.

    Automatically guesses, which mode to use. If configurable settings are
    present at /se/sjoerd/Graphs/import-params, a Window will be shown,
    giving the option to configure them.
    """
    application = window.get_application()
    settings = application.get_settings_child("import-params")
    import_dict = {mode: [] for mode in _IMPORT_MODES.keys()}
    for file in files:
        import_dict[_guess_import_mode(file)].append(file)
    modes = [mode for mode in settings.list_children() if import_dict[mode]]

    def do_import(_dialog):
        items = []
        data = window.get_data()
        style = data.get_selected_style_params()
        for mode, files in import_dict.items():
            callback = getattr(parse_file, "import_from_" + mode)
            params = settings.get_child(mode) if mode in modes else None
            for file in files:
                try:
                    items.extend(callback(params, style, file))
                except ParseError as error:
                    application.get_window().add_toast_string(error.message)
                    continue
        data.add_items(items)

    if modes:
        dialog = Graphs.ImportDialog.new(window, modes)
        dialog.connect("accept", do_import)
    else:
        do_import(None)


def _guess_import_mode(file: Gio.File) -> str:
    try:
        filename = Graphs.tools_get_filename(file)
        file_suffix = Path(filename).suffixes[-1]
    except IndexError:
        file_suffix = None
    for mode, suffix in _IMPORT_MODES.items():
        if suffix is not None and file_suffix == suffix:
            return mode
    return "columns"
