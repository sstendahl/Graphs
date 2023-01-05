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
import datetime

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Gdk, Adw
from .window import DatManWindow
import matplotlib.pyplot as plt
from . import datman, plotting_tools, item_operations, transform_data, preferences, add_equation, add_data_advanced, plot_settings

class DatManApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='se.sjoerd.DatMan',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.filename = ""
        self.datadict = {}
        self.item_rows = {}
        self.highlight = None
        self.highlights = []
        self.connect_actions()
        
    def load_preferences(self):
        plotting_tools.load_fonts(self)
        self.preferences = preferences.Preferences(self)
        self.plot_settings = plotting_tools.PlotSettings(self)

    def connect_actions(self):
        self.create_action('quit', self.on_quit_action, ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', preferences.open_preferences_window, ['<primary>p'], self)
        self.create_action('add_data', datman.open_file_dialog, ['<primary>N'], self)
        self.create_action('add_data_advanced', add_data_advanced.open_add_data_advanced_window, ['<primary><shift>N'], self)
        self.create_action('normalize_data', item_operations.normalize_data, None, self)
        self.create_action('translate_x', item_operations.translate_x, None, self)
        self.create_action('translate_y', item_operations.translate_y, None, self)
        self.create_action('multiply_x', item_operations.multiply_x, None, self)
        self.create_action('cut_data', item_operations.cut_data, None, self)
        self.create_action('multiply_y', item_operations.multiply_y, None, self)
        self.create_action('smooth', item_operations.smoothen_data, None, self)
        self.create_action('center_data', item_operations.center_data, None, self)
        self.create_action('shift_vertically', item_operations.shift_vertically, None, self)
        self.create_action('save_data', item_operations.save_data, ['<primary>S'], self)
        self.create_action('select_all', datman.select_all, ['<primary>A'], self)
        self.create_action('undo', item_operations.undo, ['<primary>Z'], self)
        self.create_action('redo', item_operations.redo, ['<primary><shift>Z'], self)
        self.create_action('select_none', datman.select_none, ['<primary><shift>A'], self)
        self.create_action('transform_data', transform_data.open_transform_window, None, self)
        self.create_action('add_equation', add_equation.open_add_equation_window, ['<primary>E'], self)
        self.create_action('select_data_toggle', plotting_tools.toggle_highlight, None, self)
        self.create_action('get_derivative', item_operations.get_derivative, None, self)
        self.create_action('get_integral', item_operations.get_integral, None, self)
        self.create_action('get_fourier', item_operations.get_fourier, None, self)
        self.create_action('get_inverse_fourier', item_operations.get_inverse_fourier, None, self)        
        self.create_action('delete_selected', datman.delete_selected, ['Delete'], self)
        self.create_action('plot_settings', plot_settings.open_plot_settings, ["<primary><shift>P"], self)
        Adw.StyleManager.get_default().connect("notify", datman.toggle_darkmode, None, self)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        self.main_window = win
        if not win:
            win = DatManWindow(application=self)
        self.load_preferences()
        datman.load_empty(self)
        # Should turn off in XML probably
        datman.turn_off_clipboard_buttons(self)
        win.maximize()
        win.present()

    def on_about_action(self, _widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Graphs',
                                application_icon='se.sjoerd.DatMan',
                                website='https://www.sjoerd.se/Graphs',
                                developer_name='Sjoerd Broekhuijsen',
                                issue_url="https://github.com/SjoerdB93/Graphs/issues",
                                version='1.3.4',
                                developers=['Sjoerd Broekhuijsen <contact@sjoerd.se>'],
                                copyright=f"© 2022-{datetime.date.today().year} Sjoerd Broekhuijsen",
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
