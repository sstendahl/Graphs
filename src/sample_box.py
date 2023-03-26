# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gtk, GLib

from graphs import graphs, ui, utilities
from graphs.edit_item import EditItemWindow


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/sample_box.ui")
class SampleBox(Gtk.Box):
    __gtype_name__ = "SampleBox"
    sample_box = Gtk.Template.Child()
    label = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()
    color_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()

    def __init__(self, parent, item, selected=False):
        super().__init__()
        self.item = item
        self.label.set_text(utilities.shorten_label(item.filename))
        if selected:
            self.check_button.set_active(True)
        self.parent = parent
        self.one_click_trigger = False
        self.time_first_click = 0
        self.gesture = Gtk.GestureClick()
        self.gesture.set_button(0)
        self.add_controller(self.gesture)
        self.edit_button.connect("clicked", self.edit)
        self.color_button.connect("clicked", self.choose_color)
        self.delete_button.connect("clicked", self.delete)
        self.check_button.connect("toggled", self.toggled)
        self.provider = Gtk.CssProvider()
        self.color_button.get_style_context().add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.update_color()

    def update_color(self):
        color = utilities.tuple_to_rgba(self.item.color)
        css = f"button {{ color: {color.to_string()}; }}"
        self.provider.load_from_data(css, -1)

    def choose_color(self, _):
        color = utilities.tuple_to_rgba(self.item.color)
        dialog = Gtk.ColorDialog()
        dialog.choose_rgba(
            self.parent.main_window, color, None, self.on_accept)

    def on_accept(self, dialog, result):
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

    def toggled(self, _):
        graphs.refresh(self.parent, False)
        ui.enable_data_dependent_buttons(
            self.parent, utilities.get_selected_keys(self.parent))

    def edit(self, _):
        EditItemWindow(self.parent, self.item)
