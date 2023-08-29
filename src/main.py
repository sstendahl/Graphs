# SPDX-License-Identifier: GPL-3.0-or-later
"""
Main application.

Classes:
    GraphsApplication
"""
import logging
from gettext import gettext as _

from gi.repository import Adw, GLib, GObject, Gio

from graphs import actions, migrate, ui
from graphs.clipboard import DataClipboard, ViewClipboard
from graphs.data import Data
from graphs.figure_settings import FigureSettings
from graphs.window import GraphsWindow

from matplotlib import font_manager


_ACTIONS = [
    "quit", "about", "preferences", "figure_settings", "add_data",
    "add_equation", "select_all", "select_none", "undo", "redo",
    "optimize_limits", "view_back", "view_forward", "export_data",
    "export_figure", "styles", "save_project", "open_project",
    "delete_selected",
]


class GraphsApplication(Adw.Application):
    """
    The main application singleton class.

    Properties:
        settings
        version: str
        name: str
        website: str
        issues: str
        author: str
        pkgdatadir: str
        data
        figure_settings
        clipboard
        view_clipboard
        mode: int (pan, zoom, select)

    Functions:
        get_data
        get_mode
        set_mode
        get_figure_settings
        set_figure_settings
        get_settings
        get_clipboard
        get_view_clipboard
    """

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

        for name in _ACTIONS:
            action = Gio.SimpleAction.new(name, None)
            action.connect(
                "activate", getattr(actions, f"{name}_action"), self,
            )
            self.add_action(action)

        settings = self.get_settings("figure")
        for val in ["left-scale", "right-scale", "top-scale", "bottom-scale"]:
            action = Gio.SimpleAction.new_stateful(
                f"change-{val}", GLib.VariantType.new("s"),
                GLib.Variant.new_string(str(settings.get_enum(f"{val}"))),
            )
            action.connect("activate", actions.change_scale, self, val)
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

        self.get_style_manager().connect(
            "notify", ui.on_style_change, None, self)
        self.get_figure_settings().connect(
            "notify::use-custom-style", ui.on_figure_style_change, self,
        )
        self.get_figure_settings().connect(
            "notify::custom-style", ui.on_figure_style_change, self,
        )
        self.get_data().connect(
            "notify::items", ui.on_items_change, self,
        )
        self.get_data().connect(
            "items-ignored", ui.on_items_ignored, self,
        )

    def do_activate(self):
        """
        Activate the application.

        We raise the application"s main window, creating it if
        necessary.
        """
        self._window = self.props.active_window
        if not self._window:
            self._window = GraphsWindow(self)
            self._window.set_title(self.props.name)
            if "(Development)" in self.props.name:
                self._window.add_css_class("devel")
            self.props.clipboard = DataClipboard(self)
            self.props.view_clipboard = ViewClipboard(self)
            ui.set_clipboard_buttons(self)
            self._window.present()

    def get_window(self):
        return self._window

    def get_data(self):
        """Get data property."""
        return self.props.data

    def get_mode(self):
        """Get mode property."""
        return self.props.mode

    def set_mode(self, mode: int):
        """Set mode property."""
        self.props.mode = mode

    def get_figure_settings(self) -> FigureSettings:
        """Get figure settings property."""
        return self.props.figure_settings

    def set_figure_settings(self, figure_settings: FigureSettings):
        """Set figure settings property."""
        self.props.figure_settings = figure_settings

    def get_settings(self, child=None):
        """
        Get the applications settings.

        If child is not specified the main node is returned.
        """
        return self.props.settings if child is None \
            else self.props.settings.get_child(child)

    def get_clipboard(self):
        """Get clipboard property."""
        return self.props.clipboard

    def get_view_clipboard(self):
        """Get view clipboard property."""
        return self.props.view_clipboard
