# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for Exporting data."""
import sys

from gi.repository import Gio, Graphs

from graphs.item import DataItem


def export_items(mode: str, file: Gio.File, items: list[Graphs.Item]) -> None:
    """Export items in specified format."""
    getattr(sys.modules[__name__], "_export_" + mode)(file, items)


def _export_columns(file: Gio.File, items: list[Graphs.Item]):
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
