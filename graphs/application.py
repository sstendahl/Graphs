# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application."""
import logging
from gettext import gettext as _

from gi.repository import Adw, GLib, GObject, Gio, Graphs, Gtk

from graphs import (
    actions,
    file_import,
    migrate,
    project,
    styles,
    ui,
    utilities,
)
from graphs.data import Data

from matplotlib import font_manager

_ACTIONS = [
    "quit",
    "about",
    "figure_settings",
    "add_data",
    "add_equation",
    "select_all",
    "select_none",
    "undo",
    "redo",
    "optimize_limits",
    "view_back",
    "view_forward",
    "export_data",
    "export_figure",
    "new_project",
    "save_project",
    "save_project_as",
    "smoothen_settings",
    "open_project",
    "delete_selected",
    "zoom_in",
    "zoom_out",
]


class PythonApplication(Graphs.Application):
    """The main application singleton class."""

    __gtype_name__ = "GraphsPythonApplication"
    __gsignals__ = {
        "project-saved": (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self, application_id, **kwargs):
        settings = Gio.Settings(application_id)
        migrate.migrate_config(settings)
        data = Data(self, settings)
        super().__init__(
            application_id=application_id,
            settings=settings,
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
            data=data,
            **kwargs,
        )
        font_list = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
        for font in font_list:
            try:
                font_manager.fontManager.addfont(font)
            except RuntimeError:
                logging.warning(_("Could not load {font}").format(font=font))

        for name in _ACTIONS:
            action = Gio.SimpleAction.new(name, None)
            action.connect(
                "activate",
                getattr(actions, f"{name}_action"),
                self,
            )
            self.add_action(action)
        figure_settings = data.get_figure_settings()
        for val in ("left-scale", "right-scale", "top-scale", "bottom-scale"):
            action = Gio.SimpleAction.new_stateful(
                f"change-{val}",
                GLib.VariantType.new("s"),
                GLib.Variant.new_string(
                    str(settings.get_child("figure").get_enum(val)),
                ),
            )
            action.connect("activate", actions.change_scale, self)
            figure_settings.connect(
                f"notify::{val}",
                lambda _x,
                param,
                action_: action_.change_state(
                    GLib.Variant.new_string(
                        str(figure_settings.get_property(param.name)),
                    ),
                ),
                action,
            )
            self.add_action(action)

        toggle_sidebar_action = Gio.SimpleAction.new_stateful(
            "toggle_sidebar",
            None,
            GLib.Variant.new_boolean(True),
        )
        toggle_sidebar_action.connect("activate", actions.toggle_sidebar, self)
        self.add_action(toggle_sidebar_action)
        self.set_accels_for_action("app.toggle_sidebar", ["F9"])

        for count, mode in enumerate(["pan", "zoom", "select"]):
            action = Gio.SimpleAction.new(f"mode_{mode}", None)
            action.connect(
                "activate",
                actions.set_mode,
                self,
                count,
            )
            self.add_action(action)
            self.set_accels_for_action(f"app.mode_{mode}", [f"F{count + 1}"])

        operation_action = Gio.SimpleAction.new(
            "app.perform_operation",
            GLib.VariantType.new("s"),
        )
        operation_action.connect("activate", actions.perform_operation, self)
        self.add_action(operation_action)

        actions_settings = settings.get_child("actions")
        for action_key in ["center", "smoothen"]:
            self.add_action(actions_settings.create_action(action_key))

        data.connect(
            "notify::items",
            ui.on_items_change,
            self,
        )
        data.connect(
            "items-ignored",
            ui.on_items_ignored,
            self,
        )

    def on_project_saved(self, _application, handler=None, *args) -> None:
        """Change unsaved state."""
        self.disconnect(self.save_handler)
        if handler == "close":
            self.quit()
        data = self.get_data()
        if handler == "open_project":
            data.props.project_file = args[0]
            data.load()
        if handler == "reset_project":
            data.reset()

    def do_open(self, files: list, nfiles: int, _hint: str) -> None:
        """Open Graphs with a File as argument."""
        self.do_activate()
        data = self.get_data()
        if nfiles == 1 and files[0].get_uri().endswith(".graphs"):
            project_file = files[0]
            if data.props.unsaved:

                def on_response(_dialog, response):
                    if response == "discard_close":
                        project.load(data, project_file)
                    if response == "save_close":
                        self.save_handler = self.connect(
                            "project-saved",
                            self.on_project_saved,
                            "open_project",
                            project_file,
                        )
                        project.save_project(self)

                dialog = Graphs.tools_build_dialog("save_changes")
                dialog.set_transient_for(self.get_window())
                dialog.connect("response", on_response)
                dialog.present()

            else:
                project.load(data, project_file)
        else:
            file_import.import_from_files(self, files)

    def close_application(self, *_args) -> None:
        """
        Intercept when closing the application.

        Will ask the user to confirm
        and save/discard open data if any unsaved changes are present.
        """
        if self.get_data().props.unsaved:

            def on_response(_dialog, response):
                if response == "discard_close":
                    self.quit()
                if response == "save_close":
                    self.save_handler = self.connect(
                        "project-saved",
                        self.on_project_saved,
                        "close",
                    )
                    project.save_project(self)

            dialog = Graphs.tools_build_dialog("save_changes")
            dialog.connect("response", on_response)
            dialog.present(self.get_window())
            return True
        self.quit()

    def do_activate(self) -> None:
        """
        Activate the application.

        We raise the application"s main window, creating it if
        necessary.
        """
        window = self.props.active_window
        if not window:
            window = Graphs.Window.new(self)
            data = self.get_data()
            binding_table = [
                ("can_undo", window.get_undo_button(), "sensitive"),
                ("can_redo", window.get_redo_button(), "sensitive"),
                ("can_view_back", window.get_view_back_button(), "sensitive"),
                (
                    "can_view_forward",
                    window.get_view_forward_button(),
                    "sensitive",
                ),
                ("project_name", window.get_content_title(), "title"),
                ("project_path", window.get_content_title(), "subtitle"),
            ]
            for prop1, obj, prop2 in binding_table:
                data.bind_property(prop1, obj, prop2, 2)
            actions = (
                "multiply_x",
                "multiply_y",
                "translate_x",
                "translate_y",
            )
            for action in actions:
                entry = window.get_property(action + "_entry")
                button = window.get_property(action + "_button")
                entry.connect(
                    "notify::text",
                    self.set_entry_css,
                    entry,
                    button,
                )
                data.connect(
                    "notify::items-selected",
                    self.set_entry_css,
                    entry,
                    button,
                )
                self.set_entry_css(None, None, entry, button)
            self.set_window(window)
            window.connect("close-request", self.close_application)
            self.set_figure_style_manager(styles.StyleManager(self))
            self.get_window().get_canvas().connect_after(
                "notify::items",
                ui.enable_axes_actions,
                self,
            )
            ui.enable_axes_actions(None, None, self)
            window.present()

    def set_entry_css(
        self,
        _object,
        _param,
        entry: Adw.EntryRow,
        button: Gtk.Button,
    ) -> None:
        """Validate text field input."""
        try:
            value = utilities.string_to_float(entry.get_text())
            if value is not None:
                entry.remove_css_class("error")
                button.set_sensitive(self.get_data().props.items_selected)
                return
        except (ValueError, TypeError):
            pass
        entry.add_css_class("error")
        button.set_sensitive(False)
