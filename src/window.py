# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gio, Gtk

@Gtk.Template(resource_path='/se/sjoerd/Graphs/ui/window.ui')
class GraphsWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'GraphsWindow'
    drawing_layout = Gtk.Template.Child()
    selection_box = Gtk.Template.Child()
    undo_button = Gtk.Template.Child()
    redo_button = Gtk.Template.Child()
    translate_x_entry = Gtk.Template.Child()
    translate_y_entry = Gtk.Template.Child()
    multiply_x_entry = Gtk.Template.Child()
    multiply_y_entry = Gtk.Template.Child()
    translate_x_button = Gtk.Template.Child()
    translate_y_button = Gtk.Template.Child()
    multiply_x_button = Gtk.Template.Child()
    multiply_y_button = Gtk.Template.Child()
    smooth_button = Gtk.Template.Child()
    fourier_button = Gtk.Template.Child()
    inverse_fourier_button = Gtk.Template.Child()
    cut_data_button = Gtk.Template.Child()
    normalize_button = Gtk.Template.Child()
    center_data_button = Gtk.Template.Child()
    save_data_button = Gtk.Template.Child()
    shift_vertically_button = Gtk.Template.Child()
    select_data_button = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    list_box = Gtk.Template.Child()
    selection_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        style_context = self.save_data_button.get_style_context()
        style_context.add_class("suggested-action")



