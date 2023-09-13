# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, GObject, Gtk, Graphs

from graphs import ui

_IGNORELIST = [
    "alpha", "color", "item_type", "uuid", "selected", "xdata", "xlabel",
    "ydata", "ylabel",
]


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/edit_item.ui")
class EditItemWindow(Adw.PreferencesWindow):
    __gtype_name__ = "GraphsEditItemWindow"
    item_selector = Gtk.Template.Child()
    name = Gtk.Template.Child()
    xposition = Gtk.Template.Child()
    yposition = Gtk.Template.Child()

    item_group = Gtk.Template.Child()
    linestyle = Gtk.Template.Child()
    linewidth = Gtk.Template.Child()
    markerstyle = Gtk.Template.Child()
    markersize = Gtk.Template.Child()

    item = GObject.Property(type=Graphs.Item)
    model = GObject.Property(type=Gtk.StringList)
    bindings = GObject.Property(type=object)

    def __init__(self, application, item):
        super().__init__(
            application=application, transient_for=application.get_window(),
            item=item, bindings=[],
            model=Gtk.StringList.new(application.get_data().get_names()),
        )
        self.item_selector.set_model(self.props.model)
        self.item_selector.set_selected(
            self.get_application().get_data().get_items().index(item),
        )
        self.present()

    @Gtk.Template.Callback()
    def on_select(self, _action, _target):
        item = self.get_application().get_data()[
            self.item_selector.get_selected()]
        if item != self.item:
            self.props.model.splice(
                self.get_application().get_data().get_items().index(self.item),
                1, [self.props.item.get_name()],
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
        self.item_group.set_visible(
            self.props.item.__gtype_name__ == "GraphsDataItem",
        )

    @Gtk.Template.Callback()
    def on_close(self, _a):
        self.get_application().get_clipboard().add()
        self.destroy()
