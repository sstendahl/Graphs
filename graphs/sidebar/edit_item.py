# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for Editing an Item."""
from gi.repository import Adw, GLib, Graphs, Gtk

from graphs import utilities
from graphs.item import DataItem, EquationItem, GeneratedDataItem

import sympy


def create_item_settings(
    edit_page: Graphs.EditItemPage,
    item: Graphs.Item,
) -> None:
    """Greate settings widgets and append them to edit_item_box."""
    if isinstance(item, GeneratedDataItem):
        box = Graphs.EditItemGeneratedDataItemBox.new()
        _setup_equation(item, box)
        for prop in ("xstart", "xstop"):
            entry = box.get_property(prop)
            entry.set_text(item.get_property(prop))
            entry.connect("changed", _on_entry_change, prop, item)
        item.bind_property(
            "steps",
            box.get_steps(),
            "value",
            1 | 2,
        )
        item.bind_property(
            "scale",
            box.get_scale(),
            "selected",
            1 | 2,
        )
        edit_page.append(box)
    if isinstance(item, DataItem):
        box = Graphs.EditItemDataItemBox.new()
        for prop in ("linestyle", "markerstyle"):
            item.bind_property(
                prop,
                box.get_property(prop),
                "selected",
                1 | 2,
            )
        for prop in ("linewidth", "markersize"):
            item.bind_property(
                prop,
                box.get_property(prop).get_adjustment(),
                "value",
                1 | 2,
            )
        edit_page.append(box)
    elif isinstance(item, EquationItem):
        box = Graphs.EditItemEquationItemBox.new()
        _setup_equation(item, box)
        item.bind_property(
            "linestyle",
            box.get_linestyle(),
            "selected",
            1 | 2,
        )
        item.bind_property(
            "linewidth",
            box.get_linewidth().get_adjustment(),
            "value",
            1 | 2,
        )
        edit_page.append(box)


def _setup_equation(item: Graphs.Item, box: Gtk.Box) -> None:
    equation_entry = box.get_equation()
    equation_entry.set_text(item.props.equation)
    equation_entry.connect("changed", _on_equation_change, item)
    box.get_simplify().connect(
        "activated",
        _on_simplify,
        item,
        equation_entry,
    )


def _on_equation_change(entry_row: Adw.EntryRow, item: Graphs.Item) -> None:
    """Handle equation change."""
    equation = entry_row.get_text()
    if utilities.validate_equation(equation):
        entry_row.remove_css_class("error")
        item.props.equation = equation
    else:
        entry_row.add_css_class("error")


def _on_simplify(_row, item: Graphs.Item, entry_row: Adw.EntryRow) -> None:
    """Simplify the equation."""
    equation = item.props.equation
    equation = str(sympy.simplify(Graphs.preprocess_equation(equation)))
    equation = Graphs.prettify_equation(equation)
    item.props.equation = equation
    entry_row.set_text(equation)


def _on_entry_change(
    entry_row: Adw.EntryRow,
    prop: str,
    item: Graphs.Item,
) -> None:
    """Handle xstart and xstop entry change."""
    value = entry_row.get_text()
    try:
        Graphs.evalutate_string(value)
        entry_row.remove_css_class("error")
        item.set_property(prop, value)
    except GLib.Error:
        entry_row.add_css_class("error")
