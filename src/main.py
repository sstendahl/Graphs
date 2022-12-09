# main.py
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

import sys
import gi
import shutil
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import DatManWindow
import matplotlib.pyplot as plt
from . import datman, plotting_tools, item_operations, transform_data, preferences

class DatManApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='se.sjoerd.DatMan',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.filename = ""
        self.datadict = {}
        self.item_rows = {}
        self.highlight = None
        plotting_tools.load_fonts(self)
        self.preferences = preferences.Preferences()
        self.connect_actions()
        print("Connected actions")

    def connect_actions(self):
        self.create_action('quit', self.on_quit_action, ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', preferences.open_preferences_window, None, self)
        self.create_action('add_data', datman.open_file_dialog, None, self)
        self.create_action('normalize_data', item_operations.normalize_data, None, self)
        self.create_action('translate_x', item_operations.translate_x, None, self)
        self.create_action('translate_y', item_operations.translate_y, None, self)
        self.create_action('multiply_x', item_operations.multiply_x, None, self)
        self.create_action('cut_data', item_operations.cut_data, None, self)
        self.create_action('multiply_y', item_operations.multiply_y, None, self)
        self.create_action('smooth', item_operations.smoothen_data, None, self)
        self.create_action('center_data', item_operations.center_data, None, self)
        self.create_action('shift_vertically', item_operations.shift_vertically, None, self)
        self.create_action('save_data', item_operations.save_data, None, self)
        self.create_action('select_all', datman.select_all, None, self)
        self.create_action('undo', item_operations.undo, None, self)
        self.create_action('redo', item_operations.redo, None, self)
        self.create_action('select_none', datman.select_none, None, self)
        self.create_action('transform_data', transform_data.open_transform_window, None, self)
        self.create_action('select_data_toggle', plotting_tools.toggle_highlight, None, self)
        Adw.StyleManager.get_default().connect("notify", datman.toggle_darkmode, None, self)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = DatManWindow(application=self)
        datman.load_empty(self)
        # Should turn off in XML probably
        datman.turn_off_clipboard_buttons(self)
        win.maximize()
        win.present()

    def on_about_action(self, _widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='DatMan',
                                application_icon='se.sjoerd.DatMan',
                                website='http://www.sjoerd.se',
                                developer_name='Sjoerd Broekhuijsen',
                                issue_url="https://github.com/SjoerdB93/DatMan/issues",
                                version='1.0.0',
                                developers=['Sjoerd Broekhuijsen <contact@sjoerd.se>'],
                                copyright='© 2022 Sjoerd Broekhuijsen',
                                license_type="GTK_LICENSE_GPL_3_0")
        about.present()

    def on_quit_action(self, _widget, _):
        self.quit()

    def create_action(self, name, callback, shortcuts=None, *args):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
            *args: Optional extra arguments
        """

        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback, *args)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = DatManApplication()

    return app.run(sys.argv)





