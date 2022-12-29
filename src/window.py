# window.py
#
# Copyright 2022 Sjoerd Broekhuijsen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gio, Gtk

@Gtk.Template(resource_path='/se/sjoerd/DatMan/window.ui')
class DatManWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'DatManWindow'
    drawing_layout = Gtk.Template.Child()
    selection_box = Gtk.Template.Child()
    sample_box = Gtk.Template.Child()
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
    cut_data_button = Gtk.Template.Child()
    select_all_button = Gtk.Template.Child()
    select_none_button = Gtk.Template.Child()
    normalize_button = Gtk.Template.Child()
    center_data_button = Gtk.Template.Child()
    save_data_button = Gtk.Template.Child()
    shift_vertically_button = Gtk.Template.Child()
    select_data_button = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)



