# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application."""
import logging
from gettext import gettext as _

from gi.repository import Adw, GLib, GObject, Gio

from graphs import actions, migrate, ui
from graphs.clipboard import DataClipboard, ViewClipboard
from graphs.data import Data
from graphs.figure_settings import FigureSettings
from graphs.window import GraphsWindow

from matplotlib import font_manager


class GraphsApplication(Adw.Application):
    """The main application singleton class."""
    settings = GObject.Property(type=Gio.Settings)
    version = GObject.Property(type=str, default="")
    name = GObject.Property(type=str, default="")
    website = GObject.Property(type=str, default="")
    issues = GObject.Property(type=str, default="")
    author = GObject.Property(type=str, default="")
    pkgdatadir = GObject.Property(type=str, default="")

    data = GObject.Property(type=Data)
    figure_settings = GObject.Property(type=FigureSettings)
    clipboard = GObject.Property(type=DataClipboard)
    view_clipboard = GObject.Property(type=ViewClipboard)
    mode = GObject.Property(type=int, default=0, minimum=0, maximum=2)

    def __init__(self, application_id, **kwargs):
        """Init the application."""
        settings = Gio.Settings(application_id)
        super().__init__(
            application_id=application_id, settings=settings,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            figure_settings=FigureSettings.new(settings.get_child("figure")),
            data=Data(self), **kwargs,
        )
        migrate.migrate_config(self)
        font_list = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
        for font in font_list:
            try:
                font_manager.fontManager.addfont(font)
            except RuntimeError:
                logging.warning(_("Could not load %s"), font)
        self.add_actions()
        self.get_style_manager().connect(
            "notify", ui.on_style_change, None, self)
        self.props.figure_settings.connect(
            "notify::use-custom-style", ui.on_figure_style_change, self,
        )
        self.props.figure_settings.connect(
            "notify::custom-style", ui.on_figure_style_change, self,
        )
        self.props.data.connect(
            "items-change", ui.on_items_change, self,
        )
        self.props.data.connect(
            "items-ignored", ui.on_items_ignored, self,
        )

    def add_actions(self):
        """Create actions, which are defined in actions.py."""
        new_actions = [
            ("quit", ["<primary>q"]),
            ("about", None),
            ("preferences", ["<primary>p"]),
            ("figure_settings", ["<primary><shift>P"]),
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
        for name, keybinds in new_actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect(
                "activate", getattr(actions, f"{name}_action"), self,
            )
            self.add_action(action)
            if keybinds:
                self.set_accels_for_action(f"app.{name}", keybinds)

        settings = self.settings.get_child("figure")
        for val in ["left-scale", "right-scale", "top-scale", "bottom-scale"]:
            string = "linear" if settings.get_enum(val) == 0 else "log"
            action = Gio.SimpleAction.new_stateful(
                f"change-{val}", GLib.VariantType.new("s"),
                GLib.Variant.new_string(string),
            )
            action.connect("activate", ui.on_scale_action, self, val)
            self.add_action(action)

        self.toggle_sidebar = Gio.SimpleAction.new_stateful(
            "toggle_sidebar", None, GLib.Variant.new_boolean(True))
        self.toggle_sidebar.connect("activate", actions.toggle_sidebar, self)
        self.add_action(self.toggle_sidebar)
        self.set_accels_for_action("app.toggle_sidebar", ["F9"])

        for count, mode in enumerate(["pan", "zoom", "select"]):
            action = Gio.SimpleAction.new(f"mode_{mode}", None)
            action.connect(
                "activate", actions.set_mode, self, count,
            )
            self.add_action(action)
            self.set_accels_for_action(f"app.mode_{mode}", [f"F{count + 1}"])

    def do_activate(self):
        """Called when the application is activated.

        We raise the application"s main window, creating it if
        necessary.
        """
        self.main_window = self.props.active_window
        if not self.main_window:
            self.main_window = GraphsWindow(self)
            self.main_window.set_title(self.name)
            if "(Development)" in self.name:
                self.main_window.add_css_class("devel")
            self.props.clipboard = DataClipboard(self)
            self.props.view_clipboard = ViewClipboard(self)
            ui.set_clipboard_buttons(self)
            self.main_window.present()

    def on_sidebar_toggle(self, _a, _b):
        visible = self.main_window.sidebar_flap.get_reveal_flap()
        self.toggle_sidebar.change_state(GLib.Variant.new_boolean(visible))

    def get_settings(self, child=None):
        return self.props.settings if child is None \
            else self.props.settings.get_child(child)
