# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application."""
import logging
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs import actions, file_import, migrate, operations, styles
from graphs.data import Data
from graphs.python_helper import PythonHelper

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
        self._python_helper = PythonHelper(self)
        self.props.python_helper = self._python_helper
        font_list = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
        for font in font_list:
            try:
                font_manager.fontManager.addfont(font)
            except RuntimeError:
                logging.warning(_("Could not load {font}").format(font=font))

        self.setup_actions()
        self.connect("action_invoked", actions.on_action_invoked)
        self.connect("operation_invoked", operations.perform_operation)

    def do_open(self, files: list, nfiles: int, _hint: str) -> None:
        """Open Graphs with a File as argument."""
        self.do_activate()
        data = self.get_data()
        if nfiles == 1 and files[0].get_uri().endswith(".graphs"):

            def load():
                data.set_file(files[0])
                data.load()

            if data.get_unsaved():

                def on_response(_dialog, response):
                    if response == "discard_close":
                        load()
                    if response == "save_close":

                        def on_save(_o, response):
                            Graphs.project_save_finish(response)
                            load()

                        Graphs.project_save(self, False, on_save)

                dialog = Graphs.tools_build_dialog("save_changes")
                dialog.connect("response", on_response)
                dialog.present(self.get_window())
            else:
                load()
        else:
            file_import.import_from_files(self, files)

    def do_activate(self) -> None:
        """
        Activate the application.

        We raise the application"s main window, creating it if
        necessary.
        """
        window = self.props.active_window
        if not window:
            window = Graphs.Window.new(self)
            self.set_window(window)
            self.set_figure_style_manager(styles.StyleManager(self))
            window.present()
