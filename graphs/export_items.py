# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for Exporting data."""
import sys

from gi.repository import Gio, Graphs

from graphs import utilities
from graphs.item import DataItem, EquationItem, GeneratedDataItem


def export_items(
    mode: str,
    file: Gio.File,
    items: list[Graphs.Item],
    figure_settings: Graphs.FigureSettings,
) -> None:
    """Export items in specified format."""
    callback = getattr(sys.modules[__name__], "_export_" + mode)
    callback(file, items, figure_settings)


def _export_columns(
    file: Gio.File,
    items: list[Graphs.Item],
    figure_settings: Graphs.FigureSettings,
) -> None:
    """Save Items in columns format."""
    if len(items) > 1:
        for item in items:
            name = f"{item.get_name()}.txt"
            _save_item(
                file.get_child_for_display_name(name),
                item,
                figure_settings,
            )
    else:
        _save_item(file, items[0], figure_settings)


def _save_item(
    file: Gio.File,
    item: DataItem | EquationItem | GeneratedDataItem,
    figure_settings: Graphs.FigureSettings,
) -> None:
    """Save Item in columns format."""
    delimiter = "\t"
    xlabel, ylabel = item.get_xlabel(), item.get_ylabel()
    stream = Gio.DataOutputStream.new(
        file.replace(None, False, Gio.FileCreateFlags.NONE, None),
    )

    xerr, yerr = None, None
    if isinstance(item, (DataItem, GeneratedDataItem)):
        xdata, ydata = item.props.data
        if isinstance(item, DataItem):
            xerr, yerr = item.props.err
    elif isinstance(item, EquationItem):
        limits = figure_settings.get_limits()
        if item.get_xposition() == 0:
            limits = [limits[0], limits[1]]
        elif item.get_xposition() == 1:
            limits = [limits[2], limits[3]]
        equation = Graphs.preprocess_equation(item.props.equation)
        xdata, ydata = utilities.equation_to_data(equation, limits)

    n_cols = 2 + (xerr is not None) + (yerr is not None)
    fmt = delimiter.join(["%.12e"] * n_cols)

    if xlabel != "" and ylabel != "":
        headers = [xlabel, ylabel]
        if xerr is not None:
            headers.append("x_err")
        if yerr is not None:
            headers.append("y_err")
        stream.put_string(delimiter.join(headers) + "\n")

    err_cols = [e for e in (xerr, yerr) if e is not None]
    for values in zip(xdata, ydata, *err_cols):
        stream.put_string(fmt % values + "\n")
    stream.close()
