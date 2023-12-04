# SPDX-License-Identifier: GPL-3.0-or-later
"""
Main application.

Classes:
    GraphsApplication
"""
import logging
from gettext import gettext as _
from pathlib import Path
from gi.repository import GLib, Gio, Graphs, Gtk

from graphs import actions, file_import, file_io, migrate, styles, ui
from graphs.data import Data

from matplotlib import font_manager


_ACTIONS = [
    "quit", "about", "figure_settings", "add_data", "add_equation",
    "select_all", "select_none", "undo", "redo", "optimize_limits",
    "view_back", "view_forward", "export_data", "export_figure",
    "save_project", "smoothen_settings", "open_project", "delete_selected",
    "zoom_in", "zoom_out",
]


class PythonApplication(Graphs.Application):
    """The main application singleton class."""
    __gtype_name__ = "GraphsPythonApplication"

    def __init__(self, application_id, **kwargs):
        """Init the application."""
        settings = Gio.Settings(application_id)
        migrate.migrate_config(settings)
        super().__init__(
            application_id=application_id, settings=settings,
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
            data=Data(self, settings), **kwargs,
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
        for val in ("left-scale", "right-scale", "top-scale", "bottom-scale"):
            action = Gio.SimpleAction.new_stateful(
                f"change-{val}", GLib.VariantType.new("s"),
                GLib.Variant.new_string(
                    str(settings.get_child("figure").get_enum(val)),
                ),
            )
            action.connect("activate", actions.change_scale, self)
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

        actions_settings = settings.get_child("actions")
        for action_key in ["center", "smoothen"]:
            self.add_action(actions_settings.create_action(action_key))

        self.get_data().connect(
            "notify::items", ui.on_items_change, self,
        )
        self.get_data().connect(
            "items-ignored", ui.on_items_ignored, self,
        )

    def do_open(self, files, nfiles, _hint):
        self.do_activate()
        if nfiles == 1 and files[0].get_uri().endswith(".graphs"):
            file_name = Path(files[0].get_basename()).stem
            try:
                project_dict = file_io.parse_json(files[0])
            except UnicodeDecodeError:
                project_dict = migrate.migrate_project(files[0])

            if self.get_data().props.empty:
                self.get_data().load_from_project_dict(project_dict, file_name)
            else:
                def on_response(_dialog, response):
                    if response == "discard":
                        self.get_data().load_from_project_dict(project_dict,
                                                               file_name)
                dialog = ui.build_dialog("discard_data")
                dialog.set_transient_for(self.get_window())
                dialog.connect("response", on_response)
                dialog.present()
                return
        else:
            file_import.import_from_files(self, files)

    def quit(self, *_arg):
        if not self.get_data().props.empty:

            def on_response(_dialog, response):
                if response == "discard_close":
                    self.get_window().destroy()
                if response == "save_close":
                    ui.save_project_dialog(self, close=True)

            dialog = ui.build_dialog("close_application")
            dialog.set_transient_for(self.get_window())
            dialog.connect("response", on_response)
            dialog.present()
            return True
        self.get_window().destroy()

    def on_key_press_event(self, _controller, keyval, _keycode, _state):
        if keyval == 65507 or keyval == 65508:  # Control_L or Control_R
            self.set_ctrl(True)
        else:  # Prevent Ctrl from being true with key combos
            self.set_ctrl(False)

    def on_key_release_event(self, _controller, _keyval, _keycode, _state):
        self.set_ctrl(False)

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
            data.bind_property("empty", window.get_item_list(), "visible", 4)
            stack_switcher = \
                Graphs.InlineStackSwitcher(stack=window.get_stack())
            stack_switcher.add_css_class("compact")
            stack_switcher.set_hexpand("true")
            window.get_stack_switcher_box().prepend(stack_switcher)
            window.set_title(self.props.name)
            window.get_content_title().set_title(_("Untitled Project"))
            self.set_window(window)
            controller = Gtk.EventControllerKey.new()
            controller.connect("key-pressed", self.on_key_press_event)
            controller.connect("key-released", self.on_key_release_event)
            window.add_controller(controller)
            window.connect("close-request", self.quit)
            if "(Development)" in self.props.name:
                window.add_css_class("devel")
            self.set_figure_style_manager(styles.StyleManager(self))
            window.present()
