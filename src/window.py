# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, GLib, GObject, Gtk


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/window.ui")
class GraphsWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GraphsWindow"
    undo_button = Gtk.Template.Child()
    redo_button = Gtk.Template.Child()
    view_back_button = Gtk.Template.Child()
    view_forward_button = Gtk.Template.Child()
    item_list = Gtk.Template.Child()
    sidebar_flap = Gtk.Template.Child()
    pan_button = Gtk.Template.Child()
    zoom_button = Gtk.Template.Child()
    select_button = Gtk.Template.Child()
    shift_vertically_button = Gtk.Template.Child()
    cut_button = Gtk.Template.Child()
    translate_x_entry = Gtk.Template.Child()
    translate_y_entry = Gtk.Template.Child()
    multiply_x_entry = Gtk.Template.Child()
    multiply_y_entry = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(application=application)
        self.get_application().get_data().bind_property(
            "items_selected", self.shift_vertically_button, "sensitive", 2,
        )
        self.get_application().bind_property("mode", self, "mode", 2)

    def set_canvas(self, canvas):
        self.toast_overlay.set_child(canvas)

    def get_canvas(self):
        widget = self.toast_overlay.get_child()
        return None if isinstance(widget, Adw.StatusPage) else widget

    @GObject.Property(type=int, default=0, minimum=0, maximum=2, flags=2)
    def mode(self):
        pass

    @mode.setter
    def mode(self, mode: int):
        self.pan_button.set_active(mode == 0)
        self.zoom_button.set_active(mode == 1)
        self.select_button.set_active(mode == 2)

    def add_toast(self, title):
        self.toast_overlay.add_toast(Adw.Toast(title=title))

    @Gtk.Template.Callback()
    def on_sidebar_toggle(self, *_args):
        self.get_application().lookup_action("toggle_sidebar").change_state(
            GLib.Variant.new_boolean(self.sidebar_flap.get_reveal_flap()),
        )

    @Gtk.Template.Callback()
    def perform_operation(self, button):
        action = self.get_application().lookup_action("app.perform_operation")
        operation = button.get_child().get_label().lower().replace(" ", "_")
        action.activate(GLib.Variant.new_string(operation))
