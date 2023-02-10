# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

@Gtk.Template(resource_path='/se/sjoerd/Graphs/ui/window.ui')
class GraphsWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'GraphsWindow'
    pan_button = Gtk.Template.Child()
    zoom_button = Gtk.Template.Child()
    select_button = Gtk.Template.Child()
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
    shift_vertically_button = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    list_box = Gtk.Template.Child()
    sidebar_flap = Gtk.Template.Child()
    derivative_button = Gtk.Template.Child()
    integral_button = Gtk.Template.Child()
    transform_data_button = Gtk.Template.Child()
    combine_data_button = Gtk.Template.Child()
    no_data_label_box = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
