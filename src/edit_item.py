# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, GObject, Gtk

from graphs import ui
from graphs.item import ItemBase

IGNORELIST = [
    "alpha", "color", "item_type", "key", "selected", "xdata", "xlabel",
    "ydata", "ylabel",
]


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/edit_item.ui")
class EditItemWindow(Adw.PreferencesWindow):
    __gtype_name__ = "EditItemWindow"
    item_selector = Gtk.Template.Child()
    name = Gtk.Template.Child()
    xposition = Gtk.Template.Child()
    yposition = Gtk.Template.Child()

    item_group = Gtk.Template.Child()
    linestyle = Gtk.Template.Child()
    linewidth = Gtk.Template.Child()
    markerstyle = Gtk.Template.Child()
    markersize = Gtk.Template.Child()

    item = GObject.Property(type=ItemBase)
    names = GObject.Property(type=object)

    def __init__(self, application, item):
        super().__init__(
            application=application, transient_for=application.main_window,
            item=item, names=application.props.data.get_names(),
        )
        items = self.props.application.props.data.props.items
        self.item_selector.set_model(Gtk.StringList.new(self.props.names))
        self.item_selector.set_selected(items.index(item))
        self.present()

    @Gtk.Template.Callback()
    def on_close(self, *_args):
        self.apply()

    @Gtk.Template.Callback()
    def on_select(self, _action, _target):
        self.apply()
        index = self.item_selector.get_selected()
        self.item = self.props.application.props.data.props.items[index]

        # If item_selector no longer matches with name, repopulate it
        names = self.props.application.props.data.get_names()
        if set(names) != set(self.props.names):
            self.props.names = names
            self.item_selector.set_model(Gtk.StringList.new(names))
            self.item_selector.set_selected(index)

    @Gtk.Template.Callback()
    def on_item_change(self, _a, _b):
        self.set_title(self.props.item.props.name)
        ui.load_values_from_dict(
            self, self.props.item.to_dict(), ignorelist=IGNORELIST,
        )
        self.item_group.set_visible(self.props.item.props.item_type == "Item")

    def apply(self):
        new_values = ui.save_values_to_dict(
            self, dir(self.props.item.props), ignorelist=IGNORELIST,
        )
        for key, value in new_values.items():
            self.props.item.set_property(key, value)
        self.props.application.props.clipboard.add()
