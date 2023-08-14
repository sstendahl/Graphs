# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, GObject, Gtk

from graphs.item import Item, ItemBase


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
        self.set_title(self.item.name)
        self.name.set_text(self.item.name)
        self.xposition.set_selected(self.item.xposition)
        self.yposition.set_selected(self.item.yposition)
        self.item_group.set_visible(False)
        if isinstance(self.item, Item):
            self.load_item_values()

    def load_item_values(self):
        self.item_group.set_visible(True)
        self.linestyle.set_selected(self.item.linestyle)
        self.linewidth.set_value(self.item.linewidth)
        self.markerstyle.set_selected(self.item.markerstyle)
        self.markersize.set_value(self.item.markersize)

    def apply(self):
        self.item.name = self.name.get_text()
        self.item.xposition = self.xposition.get_selected()
        self.item.yposition = self.yposition.get_selected()
        if isinstance(self.item, Item):
            self.apply_item_values()
        self.props.application.props.clipboard.add()

    def apply_item_values(self):
        self.item.linestyle = self.linestyle.get_selected()
        self.item.linewidth = self.linewidth.get_value()
        self.item.markerstyle = self.markerstyle.get_selected()
        self.item.markersize = self.markersize.get_value()
