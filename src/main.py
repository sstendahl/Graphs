# SPDX-License-Identifier: GPL-3.0-or-later
"""
Main application.

Classes:
    GraphsApplication
"""
import logging
from gettext import gettext as _

from gi.repository import Adw, GLib, GObject, Gio, Graphs

from graphs import actions, migrate, ui
from graphs.clipboard import DataClipboard, ViewClipboard
from graphs.data import Data
from graphs.window import GraphsWindow

from matplotlib import font_manager


_ACTIONS = [
    "quit", "about", "preferences", "figure_settings", "add_data",
    "add_equation", "select_all", "select_none", "undo", "redo",
    "optimize_limits", "view_back", "view_forward", "export_data",
    "export_figure", "styles", "save_project", "open_project",
    "delete_selected",
]


class GraphsApplication(Graphs.Application):
    """
    The main application singleton class.

    Functions:
        get_settings
    """

    def __init__(self, application_id, **kwargs):
        """Init the application."""
        settings = Gio.Settings(application_id)
        migrate.migrate_config(self)
        figure_settings = \
            Graphs.FigureSettings.new(settings.get_child("figure"))
        super().__init__(
            application_id=application_id, settings=settings,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            figure_settings=figure_settings,
            data=Data(self), **kwargs,
        )
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

        for val in ["left-scale", "right-scale", "top-scale", "bottom-scale"]:
            action = Gio.SimpleAction.new_stateful(
                f"change-{val}", GLib.VariantType.new("s"),
                GLib.Variant.new_string(
                    str(settings.get_child("figure").get_enum(val)),
                ),
            )
            action.connect(
                "activate",
                lambda action_, target: figure_settings.set_property(
                    action_.get_name()[7:], int(target.get_string()),
                ),
            )
            figure_settings.connect(
                f"notify::{val}",
                lambda _x, param, action_: action_.change_state(
                    GLib.Variant.new_string(
                        str(figure_settings.get_property(param.name)),
                    ),
                ), action,
            )
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
            "notify", ui.on_figure_style_change, self,
        )
        for prop in ["use-custom-style", "custom-style"]:
            figure_settings.connect(
                f"notify::{prop}", ui.on_figure_style_change, self,
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
        window = self.props.active_window
        if not window:
            window = GraphsWindow(self)
            self.set_window(window)
            window.set_title(self.props.name)
            if "(Development)" in self.props.name:
                window.add_css_class("devel")
            self.set_clipboard(DataClipboard(self))
            self.set_view_clipboard(ViewClipboard(self))
            ui.set_clipboard_buttons(self)
            window.present()

    def get_settings(self, child=None):
        """
        Get the applications settings.

        If child is not specified the main node is returned.
        """
        return self.props.settings if child is None \
            else self.props.settings.get_child(child)
