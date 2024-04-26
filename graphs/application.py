# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application."""
import logging
from gettext import gettext as _

from gi.repository import Adw, Gio, Graphs, Gtk

from graphs import (
    actions,
    file_import,
    migrate,
    operations,
    project,
    styles,
    utilities,
)
from graphs.data import Data
from graphs.item_box import ItemBox

from matplotlib import font_manager


class PythonApplication(Graphs.Application):
    """The main application singleton class."""

    __gtype_name__ = "GraphsPythonApplication"

    def __init__(self, application_id, **kwargs):
        settings = Gio.Settings(application_id)
        migrate.migrate_config(settings)
        data = Data(settings.get_child("figure"))
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

        Graphs.setup_actions(self)
        self.connect("action_invoked", actions.on_action_invoked)
        self.connect("operation_invoked", operations.perform_operation)

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
            if data.get_unsaved():

                def on_response(_dialog, response):
                    if response == "discard_close":
                        project.load(data, project_file)
                    if response == "save_close":
                        self.save_handler = data.connect(
                            "saved",
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
        if self.get_data().get_unsaved():

            def on_response(_dialog, response):
                if response == "discard_close":
                    self.quit()
                if response == "save_close":
                    self.save_handler = self.get_data().connect(
                        "saved",
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

            def on_items(data, _ignored):
                window.set_item_boxes([
                    ItemBox(self, item, index) for index,
                    item in enumerate(data)
                ])
                window.update_view_menu()
                data.add_view_history_state()

            data.connect("notify::items", on_items)
            window.present()

    def set_entry_css(
        self,
        _object,
        _param,
        entry: Adw.EntryRow,
        button: Gtk.Button,
    ) -> None:
        """Validate text field input."""
        button.set_sensitive(
            utilities.validate_entry(entry)[1]
            and self.get_data().props.items_selected,
        )
