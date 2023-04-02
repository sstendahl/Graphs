# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gtk, GLib, Gdk, gio

from graphs import graphs, ui, utilities
from graphs.edit_item import EditItemWindow


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/item_box.ui")
class ItemBox(Gtk.Box):
    __gtype_name__ = "ItemBox"
    label = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()
    color_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()

    def __init__(self, parent, item):
        super().__init__()
        self.item = item
        self.label.set_text(utilities.shorten_label(item.name))
        self.check_button.set_active(item.selected)
        self.parent = parent

        self.one_click_trigger = False
        self.time_first_click = 0
        self.gesture = Gtk.GestureClick()
        self.gesture.set_button(0)
        self.add_controller(self.gesture)
        self.edit_button.connect("clicked", self.edit)
        self.color_button.connect("clicked", self.choose_color)
        self.delete_button.connect("clicked", self.delete)
        self.check_button.connect("toggled", self.on_toggle)
        self.provider = Gtk.CssProvider()
        self.color_button.get_style_context().add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.update_color()
        self.drag_source = Gtk.DragSource.new()
        self.drag_source.set_actions(Gdk.DragAction.COPY)
        self.drag_source.connect('prepare', self.on_dnd_prepare)
        self.drag_source.connect('drag-begin', self.test)
        self.drag_source.connect('drag-end', self.test)
        self.add_controller(self.drag_source)

    def test(self, *args):
        print("hoi")

    def on_dnd_prepare(self, drag_source, x, y):



        content = gdk.ContentProvider.new_for_value(gobject.Value(gio.ListModel, data))
        return content

    def update_color(self):
        color = utilities.tuple_to_rgba(self.item.color)
        css = f"button {{ color: {color.to_string()}; }}"
        self.provider.load_from_data(css, -1)

    def choose_color(self, _):
        color = utilities.tuple_to_rgba(self.item.color)
        dialog = Gtk.ColorDialog()
        dialog.choose_rgba(
            self.parent.main_window, color, None, self.on_color_dialog_accept)

    def on_color_dialog_accept(self, dialog, result):
        try:
            color = dialog.choose_rgba_finish(result)
            if color is not None:
                self.item.color = utilities.rgba_to_tuple(color)
                self.update_color()
                graphs.refresh(self.parent)
        except GLib.GError:
            pass

    def delete(self, _):
        graphs.delete_item(self.parent, self.item.key, True)

    def on_toggle(self, _):
        self.item.selected = self.check_button.get_active()
        graphs.refresh(self.parent, False)
        ui.enable_data_dependent_buttons(
            self.parent, utilities.get_selected_keys(self.parent))

    def edit(self, _):
        EditItemWindow(self.parent, self.item)
