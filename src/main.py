# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application."""
import logging
import sys
from gettext import gettext as _
from inspect import getmembers, isfunction

from gi.repository import Adw, GLib, GObject, Gio

from graphs import actions, file_io, plot_styles, ui
from graphs.canvas import Canvas
from graphs.clipboard import DataClipboard, ViewClipboard
from graphs.misc import InteractionMode, PlotSettings
from graphs.window import GraphsWindow

from matplotlib import font_manager, pyplot


class GraphsApplication(Adw.Application):
    """The main application singleton class."""
    settings = GObject.Property(type=Gio.Settings)
    version = GObject.Property(type=str, default="")
    name = GObject.Property(type=str, default="")
    website = GObject.Property(type=str, default="")
    issues = GObject.Property(type=str, default="")
    author = GObject.Property(type=str, default="")
    pkgdatadir = GObject.Property(type=str, default="")
    datadict = GObject.Property(type=object)

    def __init__(self, args):
        """Init the application."""
        super().__init__(
            application_id=args[1], flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            version=args[0], name=args[2], website=args[3], issues=args[4],
            author=args[5], pkgdatadir=args[6],
            datadict={}, settings=Gio.Settings(args[1]),
        )
        font_list = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
        for font in font_list:
            try:
                font_manager.fontManager.addfont(font)
            except RuntimeError:
                logging.warning(_("Could not load %s"), font)
        self.add_actions()
        self.get_style_manager().connect(
            "notify", ui.on_style_change, None, self)

    def add_actions(self):
        """Create actions, which are defined in actions.py."""
        new_actions = [
            ("quit", ["<primary>q"]),
            ("about", None),
            ("preferences", ["<primary>p"]),
            ("plot_settings", ["<primary><shift>P"]),
            ("add_data", ["<primary>N"]),
            ("add_equation", ["<primary><alt>N"]),
            ("select_all", ["<primary>A"]),
            ("select_none", ["<primary><shift>A"]),
            ("undo", ["<primary>Z"]),
            ("redo", ["<primary><shift>Z"]),
            ("optimize_limits", ["<primary>L"]),
            ("view_back", ["<alt>Z"]),
            ("view_forward", ["<alt><shift>Z"]),
            ("export_data", ["<primary><shift>E"]),
            ("export_figure", ["<primary>E"]),
            ("plot_styles", ["<primary><alt>P"]),
            ("save_project", ["<primary>S"]),
            ("open_project", ["<primary>O"]),
            ("delete_selected", ["Delete"]),
        ]
        methods = {key: item for key, item
                   in getmembers(globals().copy()["actions"], isfunction)}
        for name, keybinds in new_actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", methods[f"{name}_action"], self)
            self.add_action(action)

            if keybinds:
                self.set_accels_for_action(f"app.{name}", keybinds)

        # TODO implement actions again
        """
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
        """

        self.toggle_sidebar = Gio.SimpleAction.new_stateful(
            "toggle_sidebar", None, GLib.Variant.new_boolean(True))
        self.toggle_sidebar.connect("activate", actions.toggle_sidebar, self)
        self.add_action(self.toggle_sidebar)
        self.set_accels_for_action("app.toggle_sidebar", ["F9"])

        self.create_mode_action("mode_pan", ["F1"],
                                InteractionMode.PAN)
        self.create_mode_action("mode_zoom", ["F2"],
                                InteractionMode.ZOOM)
        self.create_mode_action("mode_select", ["F3"],
                                InteractionMode.SELECT)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application"s main window, creating it if
        necessary.
        """
        self.main_window = self.props.active_window
        if not self.main_window:
            self.main_window = GraphsWindow(application=self)
        self.main_window.set_title(self.name)
        if "(Development)" in self.name:
            self.main_window.add_css_class("devel")
        self.plot_settings = PlotSettings(self.settings.get_child("figure"))
        pyplot.rcParams.update(
            file_io.parse_style(plot_styles.get_preferred_style(self)))
        self.canvas = Canvas(self)
        self.Clipboard = DataClipboard(self)
        self.ViewClipboard = ViewClipboard(self)
        self.main_window.toast_overlay.set_child(self.canvas)
        ui.set_clipboard_buttons(self)
        ui.enable_data_dependent_buttons(self)
        self.set_mode(None, None, InteractionMode.PAN)
        self.main_window.present()

    def set_mode(self, _action, _target, mode):
        """Set the current UI interaction mode (none, pan, zoom or select)."""
        win = self.main_window
        pan_button = win.pan_button
        zoom_button = win.zoom_button
        if mode == InteractionMode.PAN:
            pan_button.set_active(True)
            zoom_button.set_active(False)
            select = False
        elif mode == InteractionMode.ZOOM:
            pan_button.set_active(False)
            zoom_button.set_active(True)
            select = False
        elif mode == InteractionMode.SELECT:
            pan_button.set_active(False)
            zoom_button.set_active(False)
            select = True
        win.select_button.set_active(select)
        self.canvas.highlight.set_active(select)
        self.canvas.highlight.set_visible(select)
        win.cut_button.set_sensitive(select)
        for axis in self.canvas.figure.get_axes():
            axis.set_navigate_mode(mode.name if mode.name != "" else None)
        self.interaction_mode = mode
        self.canvas.draw()

    def on_sidebar_toggle(self, _a, _b):
        visible = self.main_window.sidebar_flap.get_reveal_flap()
        self.toggle_sidebar.change_state(GLib.Variant.new_boolean(visible))

    def create_axis_action(self, name, callback, preferences_key):
        """Create action for setting axis scale."""
        action = Gio.SimpleAction.new_stateful(
            name, GLib.VariantType.new("s"),
            GLib.Variant.new_string(self.preferences[preferences_key]))
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
