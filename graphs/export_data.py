# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for Exporting data."""
import contextlib
from gettext import pgettext as C_

from gi.repository import GLib, Gio, Graphs, Gtk

from graphs import utilities
from graphs.item import DataItem


def export_items(application: Graphs.Application, items: list[DataItem]):
    """Export items."""
    multiple = len(items) > 1

    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            if multiple:
                file = dialog.select_folder_finish(response)
            else:
                file = dialog.save_finish(response)
            save_columns(file, items)

    dialog = Gtk.FileDialog()
    if multiple:
        dialog.select_folder(application.get_window(), None, on_response)
    else:
        filename = f"{items[0].get_name()}.txt"
        dialog.set_initial_name(filename)
        dialog.set_filters(
            utilities.create_file_filters(
                ((C_("file-filter", "Text Files"), ["txt"]), ),
            ),
        )
        dialog.save(application.get_window(), None, on_response)


def save_columns(file: Gio.File, items: list[DataItem]) -> None:
    """Save Items in columns format."""
    if len(items) > 1:
        for item in items:
            name = f"{item.get_name()}.txt"
            _save_item(file.get_child_for_display_name(name), item)
    else:
        _save_item(file, items[0])


def _save_item(file: Gio.File, item: DataItem) -> None:
    """Save Item in columns format."""
    delimiter = "\t"
    fmt = delimiter.join(["%.12e"] * 2)
    xlabel, ylabel = item.get_xlabel(), item.get_ylabel()
    stream = Gio.DataOutputStream.new(
        file.replace(None, False, Gio.FileCreateFlags.NONE, None),
    )
    if xlabel != "" and ylabel != "":
        stream.stream(xlabel + delimiter + ylabel + "\n")
    for values in zip(item.xdata, item.ydata):
        stream.put_string(fmt % values + "\n")
    stream.close()
