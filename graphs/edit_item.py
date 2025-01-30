# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for Editing an Item."""
from gi.repository import Adw, GObject, Graphs, Gtk

from graphs import utilities
from graphs.item import DataItem, EquationItem

import sympy


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/edit-item.ui")
class EditItemDialog(Adw.Dialog):
    """Class for editing an Item."""

    __gtype_name__ = "GraphsEditItemDialog"

    name = Gtk.Template.Child()
    xposition = Gtk.Template.Child()
    yposition = Gtk.Template.Child()
    item_box = Gtk.Template.Child()

    data = GObject.Property(type=Graphs.Data)
    item = GObject.Property(type=Graphs.Item)

    def __init__(self, window: Graphs.Window, item: Graphs.Item):
        super().__init__(data=window.get_data(), item=item)
        item.bind_property("name", self, "title", 2)
        item.bind_property("name", self.name, "text", 1 | 2)
        for prop in ("xposition", "yposition"):
            item.bind_property(prop, getattr(self, prop), "selected", 1 | 2)

        if isinstance(item, DataItem):
            box = Graphs.EditItemDataItemBox.new()
            for prop in ("linestyle", "markerstyle"):
                item.bind_property(
                    prop, box.get_property(prop), "selected", 1 | 2,
                )
            for prop in ("linewidth", "markersize"):
                item.bind_property(
                    prop,
                    box.get_property(prop).get_adjustment(),
                    "value",
                    1 | 2,
                )
            self.item_box.append(box)
        elif isinstance(item, EquationItem):
            box = Graphs.EditItemEquationItemBox.new()
            self._equation_entry = box.get_equation()
            self._equation_entry.set_text(item.props.equation)
            box.get_equation().connect("changed", self.on_equation_change)
            box.get_simplify().connect("activated", self.on_simplify)
            item.bind_property(
                "linestyle", box.get_linestyle(), "selected", 1 | 2,
            )
            item.bind_property(
                "linewidth",
                box.get_linewidth().get_adjustment(),
                "value",
                1 | 2,
            )
            self.item_box.append(box)

        self.present(window)

    def on_equation_change(self, entry_row: Adw.EntryRow) -> None:
        """Handle equation change."""
        equation = entry_row.get_text()
        if utilities.validate_equation(equation):
            entry_row.remove_css_class("error")
            self.props.item.props.equation = equation
        else:
            entry_row.add_css_class("error")

    def on_simplify(self, _buttonrow) -> None:
        """Simplify the equation."""
        equation = self.props.item.props.equation
        equation = str(sympy.simplify(utilities.preprocess(equation)))
        self.props.item.props.equation = equation
        self._equation_entry.set_text(equation)

    @Gtk.Template.Callback()
    def on_close(self, _a) -> None:
        """Handle dialog closing."""
        self.props.data.add_history_state()
