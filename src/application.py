# SPDX-License-Identifier: GPL-3.0-or-later
"""
Main application.

Classes:
    GraphsApplication
"""
import logging
from gettext import gettext as _

from gi.repository import GLib, Gio, Graphs

from graphs import actions, migrate, ui
from graphs.data import Data

from matplotlib import font_manager


_ACTIONS = [
    "quit", "about", "preferences", "figure_settings", "add_data",
    "add_equation", "select_all", "select_none", "undo", "redo",
    "optimize_limits", "view_back", "view_forward", "export_data",
    "export_figure", "styles", "save_project", "open_project",
    "delete_selected", "zoom_in", "zoom_out",
]


class PythonApplication(Graphs.Application):
    """
    The main application singleton class.

    Functions:
        get_settings
    """
    __gtype_name__ = "GraphsPythonApplication"

    def __init__(self, application_id, **kwargs):
        """Init the application."""
        settings = Gio.Settings(application_id)
        migrate.migrate_config(settings)
        super().__init__(
            application_id=application_id, settings=settings,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            data=Data(self, settings),
            **kwargs,
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

        figure_settings = self.get_data().get_figure_settings()
        for val in ["left-scale", "right-scale", "top-scale", "bottom-scale"]:
            action = Gio.SimpleAction.new_stateful(
                f"change-{val}", GLib.VariantType.new("s"),
                GLib.Variant.new_string(
                    str(settings.get_child("figure").get_enum(val)),
                ),
            )
            action.connect(
                "activate", lambda action_, target:
                (figure_settings.set_property(
                 action_.get_name()[7:], int(target.get_string())),
                 self.get_window().get_canvas().get_parent().grab_focus()),
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

        toggle_sidebar_action = Gio.SimpleAction.new_stateful(
            "toggle_sidebar", None, GLib.Variant.new_boolean(True))
        toggle_sidebar_action.connect("activate", actions.toggle_sidebar, self)
        self.add_action(toggle_sidebar_action)
        self.set_accels_for_action("app.toggle_sidebar", ["F9"])

        for count, mode in enumerate(["pan", "zoom", "select"]):
            action = Gio.SimpleAction.new(f"mode_{mode}", None)
            action.connect(
                "activate", actions.set_mode, self, count,
            )
            self.add_action(action)
            self.set_accels_for_action(f"app.mode_{mode}", [f"F{count + 1}"])

        operation_action = Gio.SimpleAction.new(
            "app.perform_operation", GLib.VariantType.new("s"),
        )
        operation_action.connect("activate", actions.perform_operation, self)
        self.add_action(operation_action)

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
            window = Graphs.Window(application=self)
            self.get_data().bind_property(
                "items_selected", window.get_shift_button(), "sensitive", 2,
            )
            self.bind_property("mode", window, "mode", 2)
            data = self.get_data()
            data.bind_property(
                "can_undo", window.get_undo_button(), "sensitive", 2,
            )
            data.bind_property(
                "can_redo", window.get_redo_button(), "sensitive", 2,
            )
            data.bind_property(
                "can_view_back", window.get_view_back_button(),
                "sensitive", 2,
            )
            data.bind_property(
                "can_view_forward", window.get_view_forward_button(),
                "sensitive", 2,
            )
            stack_switcher = \
                Graphs.InlineStackSwitcher(stack=window.get_stack())
            stack_switcher.add_css_class("compact")
            stack_switcher.set_hexpand("true")
            window.get_stack_switcher_box().prepend(stack_switcher)
            window.set_title(self.props.name)
            self.set_window(window)
            if "(Development)" in self.props.name:
                window.add_css_class("devel")
            ui.reload_canvas(self)
            window.present()

    def get_settings(self, child=None):
        """
        Get the applications settings.

        If child is not specified the main node is returned.
        """
        return self.props.settings if child is None \
            else self.props.settings.get_child(child)
