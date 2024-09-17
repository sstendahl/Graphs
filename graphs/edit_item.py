# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for Editing an Item."""
from gi.repository import Adw, GObject, Graphs, Gtk

from graphs import utilities
from graphs.item import DataItem, EquationItem

_IGNORELIST = [
    "alpha",
    "color",
    "item_type",
    "selected",
    "typename",
    "uuid",
    "xdata",
    "xlabel",
    "ydata",
    "ylabel",
    "equation",
]


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/edit-item.ui")
class EditItemDialog(Adw.PreferencesDialog):
    """Class for editing an Item."""

    __gtype_name__ = "GraphsEditItemDialog"
    item_selector = Gtk.Template.Child()
    item_selector_group = Gtk.Template.Child()
    name = Gtk.Template.Child()
    xposition = Gtk.Template.Child()
    yposition = Gtk.Template.Child()

    item_group = Gtk.Template.Child()
    linestyle = Gtk.Template.Child()
    linewidth = Gtk.Template.Child()
    markerstyle = Gtk.Template.Child()
    markersize = Gtk.Template.Child()
    equation_group = Gtk.Template.Child()
    equation = Gtk.Template.Child()

    data = GObject.Property(type=Graphs.Data)
    item = GObject.Property(type=Graphs.Item)
    model = GObject.Property(type=Gtk.StringList)
    bindings = GObject.Property(type=object)

    def __init__(self, application, item):
        data = application.get_data()
        super().__init__(
            data=data,
            item=item,
            bindings=[],
            model=Gtk.StringList.new(data.get_names()),
        )
        self.item_selector_group.set_visible(data.get_n_items() > 1)
        self.item_selector.set_model(self.props.model)
        self.item_selector.set_selected(data.get_items().index(item))
        self.present(application.get_window())

        if isinstance(item, EquationItem):
            self.equation.set_text(item.props.equation)

    @Gtk.Template.Callback()
    def on_equation_change(self, entry_row) -> None:
        """Handle equation change."""
        equation = entry_row.get_text()
        if utilities.validate_equation(equation):
            entry_row.remove_css_class("error")
            self.props.item.props.equation = equation
        else:
            entry_row.add_css_class("error")

    @Gtk.Template.Callback()
    def on_select(self, _action, _target) -> None:
        """Handle Item selection."""
        item = self.props.data[self.item_selector.get_selected()]
        if item != self.item:
            self.props.model.splice(
                self.props.data.get_items().index(self.item),
                1,
                [self.props.item.get_name()],
            )
            self.props.item = item
            if isinstance(item, EquationItem):
                self.equation.set_text(item.props.equation)

    @Gtk.Template.Callback()
    def on_item_change(self, _a, _b) -> None:
        """Handle Item change."""
        item = self.props.item
        self.set_title(item.get_name())
        for binding in self.props.bindings:
            binding.unbind()
        bindings = []
        for key in dir(item.props):
            if key in _IGNORELIST:
                continue
            widget = getattr(self, key)
            if isinstance(widget, Adw.EntryRow):
                bindings.append(
                    item.bind_property(key, widget, "text", 1 | 2),
                )
            elif isinstance(widget, Adw.ComboRow):
                bindings.append(
                    item.bind_property(key, widget, "selected", 1 | 2),
                )
            elif isinstance(widget, Gtk.Scale):
                bindings.append(
                    item.bind_property(
                        key,
                        widget.get_adjustment(),
                        "value",
                        1 | 2,
                    ),
                )
        self.props.bindings = bindings
        self.markerstyle.set_visible(isinstance(item, DataItem))
        self.item_group.set_visible(isinstance(item, (DataItem, EquationItem)))
        if isinstance(item, EquationItem):
            self.equation_group.set_visible(True)
            self.markersize.set_sensitive(False)

    @Gtk.Template.Callback()
    def on_close(self, _a) -> None:
        """Handle dialog closing."""
        self.props.data.add_history_state()

    @Gtk.Template.Callback()
    def on_linestyle(self, comborow, _b) -> None:
        """Handle linestyle selection."""
        self.linewidth.set_sensitive(comborow.get_selected() != 0)

    @Gtk.Template.Callback()
    def on_markers(self, comborow, _b) -> None:
        """Handle marker selection."""
        self.markersize.set_sensitive(comborow.get_selected() != 0)
