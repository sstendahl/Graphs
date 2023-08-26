# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, GObject, Gtk

from graphs import ui
from graphs.item import ItemBase

_IGNORELIST = [
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
    model = GObject.Property(type=Gtk.StringList)
    bindings = GObject.Property(type=object)

    def __init__(self, application, item):
        super().__init__(
            application=application, transient_for=application.main_window,
            item=item, bindings=[],
            model=Gtk.StringList.new(application.props.data.get_names()),
        )
        self.item_selector.set_model(self.props.model)
        self.item_selector.set_selected(
            self.props.application.props.data.props.items.index(item),
        )
        self.present()

    @Gtk.Template.Callback()
    def on_select(self, _action, _target):
        item = self.props.application.props.data[
            self.item_selector.get_selected()]
        if item != self.item:
            self.props.model.splice(
                self.props.application.props.data.props.items.index(self.item),
                1, [self.item.name],
            )
            self.props.item = item

    @Gtk.Template.Callback()
    def on_item_change(self, _a, _b):
        self.set_title(self.props.item.props.name)
        for binding in self.props.bindings:
            binding.unbind()
        self.props.bindings = ui.bind_values_to_object(
            self.props.item, self, ignorelist=_IGNORELIST,
        )
        self.item_group.set_visible(self.props.item.props.item_type == "Item")

    @Gtk.Template.Callback()
    def on_close(self, _a):
        self.props.application.props.clipboard.add()
        self.destroy()
