# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application."""
import logging
import sys
from gettext import gettext as _
from inspect import getmembers, isfunction

from gi.repository import Adw, GLib, Gio

from graphs import (actions, file_io, plot_styles, plotting_tools, preferences,
                    ui)
from graphs.canvas import Canvas
from graphs.misc import InteractionMode, PlotSettings
from graphs.window import GraphsWindow

from matplotlib import font_manager, pyplot
from matplotlib.backend_bases import _Mode


class GraphsApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self, args):
        """Init the application."""
        self.appid = args[1]
        super().__init__(application_id=self.appid,
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.version = args[0]
        self.name = args[2]
        self.copyright = args[3]
        self.website = args[4]
        self.issues = args[5]
        self.author = args[6]
        self.pkgdatadir = args[7]
        self.datadict = {}
        self.datadict_clipboard = [{}]
        self.clipboard_pos = -1
        self.highlight = None
        font_list = font_manager.findSystemFonts(
            fontpaths=None, fontext="ttf")
        for font in font_list:
            try:
                font_manager.fontManager.addfont(font)
            except RuntimeError:
                logging.warning(_("Could not load %s"), font)
        self.preferences = preferences.Preferences(self)
        self.add_actions()
        Adw.StyleManager.get_default().connect(
            "notify", ui.on_style_change, None, self)

    def add_actions(self):
        """Create actions, which are defined in actions.py."""
        new_actions = [
            ("quit", ["<primary>q"]),
            ("about", None),
            ("preferences", ["<primary>p"]),
            ("plot_settings", ["<primary><shift>P"]),
            ("add_data", ["<primary>N"]),
            ("add_data_advanced", ["<primary><shift>N"]),
            ("add_equation", ["<primary><alt>N"]),
            ("select_all", ["<primary>A"]),
            ("select_none", ["<primary><shift>A"]),
            ("undo", ["<primary>Z"]),
            ("redo", ["<primary><shift>Z"]),
            ("restore_view", ["<primary>R"]),
            ("view_back", ["<alt>Z"]),
            ("view_forward", ["<alt><shift>Z"]),
            ("export_data", ["<primary><shift>E"]),
            ("export_figure", ["<primary>E"]),
            ("plot_styles", ["<primary><alt>P"]),
            ("save_project", ["<primary>S"]),
            ("open_project", ["<primary>O"]),
            ("delete_selected", ["Delete"]),
            ("translate_x", None),
            ("translate_y", None),
            ("multiply_x", None),
            ("multiply_y", None),
            ("normalize", None),
            ("smoothen", None),
            ("center", None),
            ("shift_vertically", None),
            ("combine", None),
            ("cut_selected", None),
            ("get_derivative", None),
            ("get_integral", None),
            ("get_fourier", None),
            ("get_inverse_fourier", None),
            ("transform", None),
        ]
        methods = {key: item for key, item
                   in getmembers(globals().copy()["actions"], isfunction)}
        for name, keybinds in new_actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", methods[f"{name}_action"], self)
            self.add_action(action)

            if keybinds:
                self.set_accels_for_action(f"app.{name}", keybinds)

        self.create_axis_action("change_left_yscale",
                                plotting_tools.change_left_yscale,
                                "plot_y_scale")
        self.create_axis_action("change_right_yscale",
                                plotting_tools.change_right_yscale,
                                "plot_right_scale")
        self.create_axis_action("change_top_xscale",
                                plotting_tools.change_top_xscale,
                                "plot_top_scale")
        self.create_axis_action("change_bottom_xscale",
                                plotting_tools.change_bottom_xscale,
                                "plot_x_scale")

        self.toggle_sidebar = Gio.SimpleAction.new_stateful(
            "toggle_sidebar", None, GLib.Variant.new_boolean(True))
        self.toggle_sidebar.connect("activate", actions.toggle_sidebar, self)
        self.add_action(self.toggle_sidebar)
        self.set_accels_for_action("app.toggle_sidebar", ["F9"])

        self.create_mode_action("mode_pan", ["<shift>P", "F1"],
                                InteractionMode.PAN)
        self.create_mode_action("mode_zoom", ["<shift>Z", "F2"],
                                InteractionMode.ZOOM)
        self.create_mode_action("mode_select", ["<shift>S", "F3"],
                                InteractionMode.SELECT)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application"s main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = GraphsWindow(application=self)
        self.main_window = win
        win.set_title(self.name)
        if "(Development)" in self.name:
            win.add_css_class("devel")
        config = self.preferences.config
        self.plot_settings = PlotSettings(config)
        pyplot.rcParams.update(
            file_io.parse_style(plot_styles.get_preferred_style(self)))
        self.canvas = Canvas(self)
        win.toast_overlay.set_child(self.canvas)
        win.redo_button.set_sensitive(False)
        win.undo_button.set_sensitive(False)
        ui.enable_data_dependent_buttons(self)
        self.set_mode(None, None, InteractionMode.PAN)
        win.present()

    def set_mode(self, _action, _target, mode):
        """Set the current UI interaction mode (none, pan, zoom or select)."""
        win = self.main_window
        pan_button = win.pan_button
        zoom_button = win.zoom_button
        if mode == InteractionMode.PAN:
            self.canvas.dummy_toolbar.mode = _Mode.PAN
            pan_button.set_active(True)
            zoom_button.set_active(False)
            select = False
        elif mode == InteractionMode.ZOOM:
            self.canvas.dummy_toolbar.mode = _Mode.ZOOM
            pan_button.set_active(False)
            zoom_button.set_active(True)
            select = False
        elif mode == InteractionMode.SELECT:
            self.canvas.dummy_toolbar.mode = _Mode.NONE
            pan_button.set_active(False)
            zoom_button.set_active(False)
            select = True
        win.select_button.set_active(select)
        self.canvas.highlight.set_active(select)
        self.canvas.highlight.set_visible(select)
        win.cut_button.set_sensitive(select)
        for axis in self.canvas.figure.get_axes():
            axis.set_navigate_mode(
                self.canvas.dummy_toolbar.mode._navigate_mode)
        self.interaction_mode = mode
        self.canvas.draw()

    def on_sidebar_toggle(self, _a, _b):
        visible = self.main_window.sidebar_flap.get_reveal_flap()
        self.toggle_sidebar.change_state(GLib.Variant.new_boolean(visible))

    def create_axis_action(self, name, callback, config_key):
        """Create action for setting axis scale."""
        config = self.preferences.config[config_key]
        action = Gio.SimpleAction.new_stateful(
            name, GLib.VariantType.new("s"), GLib.Variant.new_string(config))
        action.connect("activate", callback, self)
        self.add_action(action)

    def create_mode_action(self, name, shortcuts, mode):
        """Create action for mode setting."""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", self.set_mode, mode)
        self.add_action(action)
        self.set_accels_for_action(f"app.{name}", shortcuts)


def main(args):
    """The application"s entry point."""
    app = GraphsApplication(args)

    return app.run(sys.argv)
