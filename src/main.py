# SPDX-License-Identifier: GPL-3.0-or-later
import sys

from gi.repository import Gio, Adw, GLib
from matplotlib.backend_bases import _Mode

from . import graphs, actions, plotting_tools, item_operations, transform_data, preferences, add_equation, add_data_advanced, plot_settings, ui
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
        self.create_action('quit', actions.quit_action, ['<primary>q'])
        self.create_action('about', actions.about_action)
        self.create_action('preferences', actions.preferences_action, ['<primary>p'])
        self.create_action('plot_settings', actions.plot_settings_action, ["<primary><shift>P"])
        self.create_action('add_data', actions.add_data_action, ['<primary>N'])
        self.create_action('add_data_advanced', actions.add_data_advanced_action, ['<primary><shift>N'])
        self.create_action('add_equation', actions.add_equation_action, ['<primary><alt>N'])
        self.create_action('select_all', actions.select_all_action, ['<primary>A'])
        self.create_action('select_none', actions.select_none_action, ['<primary><shift>A'])
        self.create_action('undo', item_operations.undo, ['<primary>Z'])
        self.create_action('redo', item_operations.redo, ['<primary><shift>Z'])
        self.create_action('restore_view', plotting_tools.restore_view, ['<primary>R'])
        self.create_action('view_back', plotting_tools.view_back, ['<alt>Z'])
        self.create_action('view_forward', plotting_tools.view_forward, ['<alt><shift>Z'])
        self.create_action('export_data', item_operations.export_data, ['<primary><shift>E'])
        self.create_action('export_figure', ui.export_figure, ["<primary>E"])
        self.create_action('save_project', ui.save_project_dialog, ['<primary>S'])
        self.create_action('open_project', ui.open_file_dialog, ['<primary>O'], True)
        self.create_action('normalize_data', item_operations.normalize_data)
        self.create_action('translate_x', item_operations.translate_x)
        self.create_action('translate_y', item_operations.translate_y)
        self.create_action('combine_data', item_operations.combine_data)
        self.create_action('multiply_x', item_operations.multiply_x)
        self.create_action('cut_data', item_operations.cut_data)
        self.create_action('multiply_y', item_operations.multiply_y)
        self.create_action('smooth', item_operations.smoothen_data)
        self.create_action('center_data', item_operations.center_data)
        self.create_action('shift_vertically', item_operations.shift_vertically)
        self.create_action('transform_data', transform_data.open_transform_window)
        self.create_action('get_derivative', item_operations.get_derivative)
        self.create_action('get_integral', item_operations.get_integral)
        self.create_action('get_fourier', item_operations.get_fourier)
        self.create_action('get_inverse_fourier', item_operations.get_inverse_fourier)
        self.create_action('delete_selected', graphs.delete_selected, ['Delete'])

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
        action.connect("activate", callback, self, *args)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

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


