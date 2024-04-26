# SPDX-License-Identifier: GPL-3.0-or-later
"""Some UI utilities."""
import contextlib
from gettext import pgettext as C_

from gi.repository import GLib, Graphs, Gtk

from graphs import file_import, misc, utilities


def add_data_dialog(application: Graphs.Application) -> None:
    """Show add data dialog."""

    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            file_import.import_from_files(
                application,
                dialog.open_multiple_finish(response),
            )

    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters((
            (
                C_("file-filter", "Supported files"),
                ["xy", "dat", "txt", "csv", "xrdml", "xry", "graphs"],
            ),
            (C_("file-filter", "ASCII files"), ["xy", "dat", "txt", "csv"]),
            (C_("file-filter", "PANalytical XRDML"), ["xrdml"]),
            (C_("file-filter", "Leybold xry"), ["xry"]),
            misc.GRAPHS_PROJECT_FILE_FILTER_TEMPLATE,
        )),
    )
    dialog.open_multiple(application.get_window(), None, on_response)


def validate_entry(entry: Gtk.Editable) -> float:
    """Validate an entry for having a parsable bool value."""
    value = utilities.string_to_float(entry.get_text())
    is_valid = value is not None
    if is_valid:
        entry.remove_css_class("error")
    else:
        entry.add_css_class("error")
    return is_valid, value
