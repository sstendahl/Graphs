# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, GLib, Gtk


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/window.ui")
class GraphsWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GraphsWindow"
    undo_button = Gtk.Template.Child()
    redo_button = Gtk.Template.Child()
    item_list = Gtk.Template.Child()
    sidebar_flap = Gtk.Template.Child()
    pan_button = Gtk.Template.Child()
    zoom_button = Gtk.Template.Child()
    select_button = Gtk.Template.Child()
    shift_vertically_button = Gtk.Template.Child()
    normalize_button = Gtk.Template.Child()
    smooth_button = Gtk.Template.Child()
    center_button = Gtk.Template.Child()
    combine_button = Gtk.Template.Child()
    cut_button = Gtk.Template.Child()
    translate_x_entry = Gtk.Template.Child()
    translate_x_button = Gtk.Template.Child()
    translate_y_entry = Gtk.Template.Child()
    translate_y_button = Gtk.Template.Child()
    multiply_x_entry = Gtk.Template.Child()
    multiply_x_button = Gtk.Template.Child()
    multiply_y_entry = Gtk.Template.Child()
    multiply_y_button = Gtk.Template.Child()
    derivative_button = Gtk.Template.Child()
    integral_button = Gtk.Template.Child()
    fourier_button = Gtk.Template.Child()
    inverse_fourier_button = Gtk.Template.Child()
    transform_button = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def add_toast(self, title):
        self.toast_overlay.add_toast(Adw.Toast(title=title))

    @Gtk.Template.Callback()
    def on_sidebar_toggle(self, *_args):
        self.get_application().toggle_sidebar.change_state(
            GLib.Variant.new_boolean(self.sidebar_flap.get_reveal_flap()))
