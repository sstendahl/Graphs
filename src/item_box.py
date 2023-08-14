# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
from gettext import gettext as _

from gi.repository import Adw, GLib, GObject, Gdk, Gtk

from graphs.edit_item import EditItemWindow
from graphs.item import ItemBase


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/item_box.ui")
class ItemBox(Gtk.Box):
    __gtype_name__ = "ItemBox"
    label = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    color_button = Gtk.Template.Child()

    application = GObject.Property(type=Adw.Application)
    item = GObject.Property(type=ItemBase)

    def __init__(self, application, item):
        super().__init__(application=application, item=item)
        self.props.item.bind_property("name", self.label, "label", 2)
        self.props.item.bind_property(
            "selected", self.check_button, "active", 1 | 2)

        self.gesture = Gtk.GestureClick()
        self.gesture.set_button(0)
        self.add_controller(self.gesture)
        self.provider = Gtk.CssProvider()
        self.color_button.get_style_context().add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.drag_source = Gtk.DragSource.new()
        self.drag_source.set_actions(Gdk.DragAction.COPY)
        self.drag_source.connect("prepare", self.on_dnd_prepare)
        self.drop_source = Gtk.DropTarget.new(str, Gdk.DragAction.COPY)
        self.drop_source.key = item.key
        self.drop_source.connect("drop", self.on_dnd_drop)

        self.item.connect("notify::color", self.on_color_change)
        self.on_color_change(self.props.item, None)

        self.add_controller(self.drag_source)
        self.add_controller(self.drop_source)

    def on_dnd_drop(self, drop_target, value, _x, _y):
        # Handle the dropped data here
        self.props.application.props.data.change_position(
            drop_target.key, value)
        self.props.application.props.clipboard.add()
        self.props.application.props.view_clipboard.add()

    def on_dnd_prepare(self, drag_source, x, y):
        snapshot = Gtk.Snapshot.new()
        self.do_snapshot(self, snapshot)
        paintable = snapshot.to_paintable()
        drag_source.set_icon(paintable, int(x), int(y))

        data = self.props.item.key
        return Gdk.ContentProvider.new_for_value(data)

    def on_color_change(self, item, _ignored):
        self.provider.load_from_data(
            f"button {{ color: {item.color}; opacity: {item.alpha};}}", -1)

    @Gtk.Template.Callback()
    def choose_color(self, _):
        dialog = Gtk.ColorDialog()
        dialog.choose_rgba(
            self.props.application.main_window, self.props.item.get_color(),
            None, self.on_color_dialog_accept)

    def on_color_dialog_accept(self, dialog, result):
        with contextlib.suppress(GLib.GError):
            color = dialog.choose_rgba_finish(result)
            if color is not None:
                self.props.item.set_color(color)
                self.props.application.props.clipboard.add()

    @Gtk.Template.Callback()
    def delete(self, _button):
        name = self.props.item.props.name
        self.props.application.props.data.delete_items([self.props.item])
        self.props.application.main_window.add_toast(
            _("Deleted {name}").format(name=name),
        )

    @Gtk.Template.Callback()
    def edit(self, _):
        EditItemWindow(self.props.application, self.props.item)
