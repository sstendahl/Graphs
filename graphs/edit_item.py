# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, GObject, Graphs, Gtk

from graphs import item, ui

_IGNORELIST = [
    "alpha",
    "color",
    "item_type",
    "uuid",
    "selected",
    "xdata",
    "xlabel",
    "ydata",
    "ylabel",
]


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/edit_item.ui")
class EditItemDialog(Adw.PreferencesDialog):
    __gtype_name__ = "GraphsEditItemDialog"
    item_selector = Gtk.Template.Child()
    name = Gtk.Template.Child()
    xposition = Gtk.Template.Child()
    yposition = Gtk.Template.Child()

    item_group = Gtk.Template.Child()
    linestyle = Gtk.Template.Child()
    linewidth = Gtk.Template.Child()
    markerstyle = Gtk.Template.Child()
    markersize = Gtk.Template.Child()

    data = GObject.Property(type=Graphs.DataInterface)
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
        self.item_selector.set_model(self.props.model)
        self.item_selector.set_selected(data.get_items().index(item))
        self.present(application.get_window())

    @Gtk.Template.Callback()
    def on_select(self, _action, _target) -> None:
        item = self.props.data[self.item_selector.get_selected()]
        if item != self.item:
            self.props.model.splice(
                self.props.data.get_items().index(self.item),
                1,
                [self.props.item.get_name()],
            )
            self.props.item = item

    @Gtk.Template.Callback()
    def on_item_change(self, _a, _b) -> None:
        self.set_title(self.props.item.get_name())
        for binding in self.props.bindings:
            binding.unbind()
        self.props.bindings = ui.bind_values_to_object(
            self.props.item,
            self,
            ignorelist=_IGNORELIST,
        )
        self.item_group.set_visible(isinstance(self.props.item, item.DataItem))

    @Gtk.Template.Callback()
    def on_close(self, _a) -> None:
        self.props.data.add_history_state()

    @Gtk.Template.Callback()
    def on_linestyle(self, comborow, _b) -> None:
        self.linewidth.set_sensitive(comborow.get_selected() != 0)

    @Gtk.Template.Callback()
    def on_markers(self, comborow, _b) -> None:
        self.markersize.set_sensitive(comborow.get_selected() != 0)
