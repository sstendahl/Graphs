# SPDX-License-Identifier: GPL-3.0-or-later
import sys

from gi.repository import Gio, Adw, GLib
from matplotlib.backend_bases import _Mode
from inspect import getmembers, isfunction

from . import actions, plotting_tools, preferences, graphs, ui
from .misc import InteractionMode
from .window import GraphsWindow

class GraphsApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='se.sjoerd.Graphs',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.datadict = dict()        
        self.filename = ""
        self.highlight = None
        self.highlights = []        
        self.item_rows = dict()
        self.sample_menu = dict()
        self.load_preferences()
        self.connect_actions()
        
    def load_preferences(self):
        plotting_tools.load_fonts(self)
        self.preferences = preferences.Preferences(self)
        self.plot_settings = plotting_tools.PlotSettings(self)

    def connect_actions(self):
        """
        To create an action, add name and keybinds to the list and implement a function in actions.py
        """
        new_actions = [
        ('quit', ['<primary>q']),
        ('about', None),
        ('preferences', ['<primary>p']),
        ('plot_settings', ["<primary><shift>P"]),
        ('add_data', ['<primary>N']),
        ('add_data_advanced', ['<primary><shift>N']),
        ('add_equation', ['<primary><alt>N']),
        ('select_all', ['<primary>A']),
        ('select_none', ['<primary><shift>A']),
        ('undo', ['<primary>Z']),
        ('redo', ['<primary><shift>Z']),
        ('restore_view', ['<primary>R']),
        ('view_back', ['<alt>Z']),
        ('view_forward', ['<alt><shift>Z']),
        ('export_data', ['<primary><shift>E']),
        ('export_figure', ["<primary>E"]),
        ('save_project', ['<primary>S']),
        ('open_project', ['<primary>O']),
        ('delete_selected', ['Delete']),
        ('translate_x', None),
        ('translate_y', None),
        ('multiply_x', None),
        ('multiply_y', None),
        ('normalize', None),
        ('smoothen', None),
        ('center', None),
        ('shift_vertically', None),
        ('combine', None),
        ('cut_selected', None),
        ('get_derivative', None),
        ('get_integral', None),
        ('get_fourier', None),
        ('get_inverse_fourier', None)
        ]
        methods = dict()
        for key, item in getmembers(globals().copy()["actions"], isfunction):
            methods[key] = item
        for name, keybinds in new_actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", methods[f'{name}_action'], self)
            self.add_action(action)
            if keybinds:
                self.set_accels_for_action(f"app.{name}", keybinds)

        self.create_axis_action('change_left_yscale', plotting_tools.change_left_yscale, 'plot_Y_scale')
        self.create_axis_action('change_right_yscale', plotting_tools.change_right_yscale, 'plot_right_scale')
        self.create_axis_action('change_top_xscale', plotting_tools.change_top_xscale, 'plot_top_scale')
        self.create_axis_action('change_bottom_xscale', plotting_tools.change_bottom_xscale, 'plot_X_scale')

        toggle_sidebar = Gio.SimpleAction.new_stateful("toggle_sidebar", None, GLib.Variant.new_boolean(True))
        toggle_sidebar.connect("activate", ui.toggle_sidebar, self)
        self.add_action(toggle_sidebar)
        self.set_accels_for_action("app.toggle_sidebar", ['F9'])

        self.create_mode_action('mode_pan', ['<shift>P', 'F1'], InteractionMode.PAN)
        self.create_mode_action('mode_zoom', ['<shift>Z', 'F2'], InteractionMode.ZOOM)
        self.create_mode_action('mode_select', ['<shift>S', 'F3'], InteractionMode.SELECT)

        Adw.StyleManager.get_default().connect("notify", ui.toggle_darkmode, None, self)

    def do_activate(self):
        """Called when the application is activated
        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = GraphsWindow(application=self)
        self.main_window = win
        graphs.load_empty(self)
        ui.disable_clipboard_buttons(self)
        ui.enable_data_dependent_buttons(self, False)
        self.set_mode(None, None, InteractionMode.PAN)
        win.maximize()
        win.present()

    def set_mode(self, action, target, mode):
        """
        Set the current UI interaction mode (none, pan, zoom or select)
        """
        win = self.main_window
        pan_button = win.pan_button
        zoom_button = win.zoom_button
        select_button = win.select_button
        cut_button = win.cut_data_button
        if self.highlight is None:
            plotting_tools.define_highlight(self)
        highlight = self.highlight
        if(mode == InteractionMode.PAN):
            self.dummy_toolbar.mode = _Mode.PAN
            pan_button.set_active(True)
            zoom_button.set_active(False)
            select_button.set_active(False)
            cut_button.set_sensitive(False)
            highlight.set_visible(False)
            highlight.set_active(False)
        elif(mode == InteractionMode.ZOOM):
            self.dummy_toolbar.mode = _Mode.ZOOM
            pan_button.set_active(False)
            zoom_button.set_active(True)
            select_button.set_active(False)
            cut_button.set_sensitive(False)
            highlight.set_visible(False)
            highlight.set_active(False)
        elif(mode == InteractionMode.SELECT):
            self.dummy_toolbar.mode = _Mode.NONE
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

    def create_axis_action(self, name, callback, config_key):
        action = Gio.SimpleAction.new_stateful(name, GLib.VariantType.new("s"), GLib.Variant.new_string(self.preferences.config[config_key]))
        action.connect("activate", callback, self)
        self.add_action(action)

    def create_mode_action(self, name, shortcuts, mode):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", self.set_mode, mode)
        self.add_action(action)
        self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = GraphsApplication()
    app.version = version

    return app.run(sys.argv)


