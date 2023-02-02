# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import gi
import shutil
import os
import datetime

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Gdk, Adw
from .window import GraphsWindow
import matplotlib.pyplot as plt
from matplotlib.backend_bases import _Mode
from . import graphs, plotting_tools, item_operations, transform_data, preferences, add_equation, add_data_advanced, plot_settings
from .utilities import InteractionMode

class GraphsApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='se.sjoerd.Graphs',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.datadict = {}        
        self.filename = ""
        self.highlight = None
        self.highlights = []        
        self.item_rows = {}
        self.sample_menu = {}
        self.connect_actions()
        
    def load_preferences(self):
        plotting_tools.load_fonts(self)
        self.preferences = preferences.Preferences(self)
        self.plot_settings = plotting_tools.PlotSettings(self)

    def connect_actions(self):
        self.create_action('quit', self.on_quit_action, ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('toggle_sidebar', self.toggle_sidebar, None)
        self.create_action('mode_none', self.set_mode, None, InteractionMode.NONE)
        self.create_action('mode_pan', self.set_mode, None, InteractionMode.PAN)
        self.create_action('mode_zoom', self.set_mode, None, InteractionMode.ZOOM)
        self.create_action('mode_select', self.set_mode, None, InteractionMode.SELECT)
        self.create_action('preferences', preferences.open_preferences_window, ['<primary>p'], self)
        self.create_action('add_data', graphs.open_file_dialog, ['<primary>N'], self)
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
        self.create_action('select_all', graphs.select_all, ['<primary>A'], self)
        self.create_action('undo', item_operations.undo, ['<primary>Z'], self)
        self.create_action('redo', item_operations.redo, ['<primary><shift>Z'], self)
        self.create_action('select_none', graphs.select_none, ['<primary><shift>A'], self)
        self.create_action('transform_data', transform_data.open_transform_window, None, self)
        self.create_action('add_equation', add_equation.open_add_equation_window, ['<primary>E'], self)
        self.create_action('get_derivative', item_operations.get_derivative, None, self)
        self.create_action('get_integral', item_operations.get_integral, None, self)
        self.create_action('get_fourier', item_operations.get_fourier, None, self)
        self.create_action('get_inverse_fourier', item_operations.get_inverse_fourier, None, self)        
        self.create_action('delete_selected', graphs.delete_selected, ['Delete'], self)
        self.create_action('plot_settings', plot_settings.open_plot_settings, ["<primary><shift>P"], self)
        self.create_action('change_xscale', plotting_tools.change_xscale, None, self)
        self.create_action('change_yscale', plotting_tools.change_yscale, None, self)
        self.create_action('export_data', plotting_tools.export_data, ["<primary><shift>E"], self)
        self.create_action('restore_view', plotting_tools.restore_view, None, self)
        self.create_action('view_forward', plotting_tools.view_forward, None, self)
        self.create_action('view_back', plotting_tools.view_back, None, self)

        Adw.StyleManager.get_default().connect("notify", graphs.toggle_darkmode, None, self)

    def do_activate(self):
        """Called when the application is activated
        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = GraphsWindow(application=self)
        self.main_window = win
        self.load_preferences()
        graphs.load_empty(self)
        graphs.disable_clipboard_buttons(self)
        graphs.enable_data_dependent_buttons(self, False)
        self.set_mode(None, None, InteractionMode.NONE)
        win.maximize()
        win.present()

    def on_about_action(self, widget, shortcut):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Graphs',
                                application_icon='se.sjoerd.Graphs',
                                website='https://www.sjoerd.se/Graphs',
                                developer_name='Sjoerd Broekhuijsen',
                                issue_url="https://github.com/SjoerdB93/Graphs/issues",
                                version=self.version,
                                developers=[
                                'Sjoerd Broekhuijsen <contact@sjoerd.se>',
                                'Christoph Kohnen <christoph.kohnen@disroot.org>'
                                ],
                                copyright=f"© 2022-{datetime.date.today().year} Sjoerd Broekhuijsen",
                                license_type="GTK_LICENSE_GPL_3_0")
        about.present()

    def on_quit_action(self, widget, shortcut):
        self.quit()

    def toggle_sidebar(self, widget, shortcut):
        win = self.main_window
        flap = win.sidebar_flap
        enabled = not flap.get_reveal_flap()
        flap.set_reveal_flap(enabled)
        win.selection_button.set_visible(enabled)

    def set_mode(self, widget, shortcut, mode):
        """
        Set the current UI interaction mode (none, pan, zoom or select)
        """
        win = self.main_window
        none_button = win.none_button
        pan_button = win.pan_button
        zoom_button = win.zoom_button
        select_button = win.select_button
        cut_button = win.cut_data_button
        if self.highlight == None:
            plotting_tools.define_highlight(self)
        highlight = self.highlight
        if(mode == InteractionMode.NONE):
            self.dummy_toolbar.mode = _Mode.NONE
            none_button.set_active(True)
            pan_button.set_active(False)
            zoom_button.set_active(False)
            select_button.set_active(False)
            cut_button.set_sensitive(False)
            highlight.set_visible(False)
            highlight.set_active(False)
        elif(mode == InteractionMode.PAN):
            self.dummy_toolbar.mode = _Mode.PAN
            none_button.set_active(False)
            pan_button.set_active(True)
            zoom_button.set_active(False)
            select_button.set_active(False)
            cut_button.set_sensitive(False)
            highlight.set_visible(False)
            highlight.set_active(False)
        elif(mode == InteractionMode.ZOOM):
            self.dummy_toolbar.mode = _Mode.ZOOM
            none_button.set_active(False)
            pan_button.set_active(False)
            zoom_button.set_active(True)
            select_button.set_active(False)
            cut_button.set_sensitive(False)
            highlight.set_visible(False)
            highlight.set_active(False)
        elif(mode == InteractionMode.SELECT):
            self.dummy_toolbar.mode = _Mode.NONE
            none_button.set_active(False)
            pan_button.set_active(False)
            zoom_button.set_active(False)
            select_button.set_active(True)
            cut_button.set_sensitive(True)
            highlight.set_visible(True)
            highlight.set_active(True)
        for axis in self.canvas.figure.get_axes():
            axis.set_navigate_mode(self.dummy_toolbar.mode._navigate_mode)
        self._mode = mode
        self.canvas.draw()

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
    app = GraphsApplication()
    app.version = version

    return app.run(sys.argv)


