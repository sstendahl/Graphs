# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
from gettext import gettext as _

from gi.repository import Adw, GLib, GObject, Gdk, Gio, Graphs, Gtk

from graphs import utilities
from graphs.curve_fitting import CurveFittingWindow
from graphs.edit_item import EditItemWindow


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/item_box.ui")
class ItemBox(Gtk.Box):
    __gtype_name__ = "GraphsItemBox"
    label = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    color_button = Gtk.Template.Child()

    application = GObject.Property(type=Adw.Application)
    item = GObject.Property(type=Graphs.Item)
    index = GObject.Property(type=int)

    def __init__(self, application, item):
        super().__init__(
            application=application, item=item,
            index=application.get_data().index(item),
        )
        self.props.item.bind_property("name", self, "name", 2)
        self.props.item.bind_property(
            "selected", self.check_button, "active", 2,
        )
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
        self.drop_source.index = str(self.props.index)
        self.drop_source.connect("drop", self.on_dnd_drop)

        self.item.connect("notify::color", self.on_color_change)
        self.on_color_change(self.props.item, None)

        self.add_controller(self.drag_source)
        self.add_controller(self.drop_source)
        self.add_actions()

    def add_actions(self):
        data = self.get_application().get_data()
        action_list = ["edit", "delete", "curve_fitting"]
        if data.index(self.item) > 0:
            action_list += ["move_up"]
        if data.index(self.item) + 1 < len(data.get_items()):
            action_list += ["move_down"]
        action_group = Gio.SimpleActionGroup()

        # Set the action group for the widget
        for name in action_list:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", getattr(self, f"{name}"))
            action_group.add_action(action)
        self.insert_action_group("item_box", action_group)

    def _change_position(self, source_index, target_index):
        application = self.get_application()
        data = application.get_data()
        data.change_position(target_index, source_index)
        data.add_history_state()
        application.get_view_clipboard().add()

    def on_dnd_drop(self, drop_target, value, _x, _y):
        # Handle the dropped data here
        self._change_position(int(value), int(drop_target.index))

    def on_dnd_prepare(self, drag_source, x, y):
        snapshot = Gtk.Snapshot.new()
        self.do_snapshot(self, snapshot)
        paintable = snapshot.to_paintable()
        drag_source.set_icon(paintable, int(x), int(y))
        return Gdk.ContentProvider.new_for_value(str(self.props.index))

    def on_color_change(self, item, _ignored):
        self.provider.load_from_data(
            "button { "
            f"color: {item.get_color()}; "
            f"opacity: {item.get_alpha()}; "
            "}", -1,
        )

    def curve_fitting(self, _action, _shortcut):
        CurveFittingWindow(self.get_application(), self.props.item)

    def move_up(self, _action, _shortcut):
        self._change_position(self.props.index, self.props.index - 1)

    def move_down(self, _action, _shortcut):
        self._change_position(self.props.index, self.props.index + 1)

    @Gtk.Template.Callback()
    def on_toggle(self, _a, _b):
        new_value = self.check_button.get_active()
        if self.props.item.props.selected != new_value:
            self.props.item.props.selected = new_value
            self.get_application().get_data().add_history_state()

    @Gtk.Template.Callback()
    def choose_color(self, _):
        rgba = utilities.hex_to_rgba(self.props.item.get_color())
        rgba.alpha = self.props.item.get_alpha()
        dialog = Gtk.ColorDialog()
        dialog.choose_rgba(
            self.get_application().get_window(), rgba,
            None, self.on_color_dialog_accept)

    def on_color_dialog_accept(self, dialog, result):
        with contextlib.suppress(GLib.GError):
            color = dialog.choose_rgba_finish(result)
            if color is not None:
                self.props.item.set_color(utilities.rgba_to_hex(color))
                self.props.item.set_alpha(color.alpha)
                self.get_application().get_data().add_history_state()

    def delete(self, _action, _shortcut):
        name = self.props.item.props.name
        self.get_application().get_data().delete_items([self.props.item])
        toast = Adw.Toast.new(_("Deleted {name}").format(name=name))
        toast.set_button_label("Undo")
        toast.set_action_name("app.undo")
        self.get_application().get_window().add_toast(toast)

    def edit(self, _action, _shortcut):
        EditItemWindow(self.get_application(), self.props.item)

    @GObject.Property(type=str, default="")
    def name(self) -> str:
        return self.label.get_label()

    @name.setter
    def name(self, name: str):
        self.label.set_label(utilities.shorten_label(name))

    def get_application(self):
        """Get application property."""
        return self.props.application
