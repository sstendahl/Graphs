# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for importing data from files."""
import logging
from gettext import gettext as _
from pathlib import Path

from gi.repository import Gee, Graphs, Gtk

from graphs.file_import import parsers
from graphs.misc import ParseError


_REQUESTS = (
    "guess_import_mode",
    "init_import_settings",
    "load_mode_settings",
    "import",
)


class DataImporter(Graphs.DataImporter):
    """Class for importing data."""

    __gtype_name__ = "GraphsPythonDataImporter"

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application)
        for request in _REQUESTS:
            request = request + "-request"
            self.connect(
                request,
                getattr(self, "_on_" + request.replace("-", "_")),
            )

        parsers.register_parsers()
        self.setup(parsers.list_parsers())

    @staticmethod
    def _on_guess_import_mode_request(
        self,
        settings: Graphs.ImportSettings,
    ) -> int:
        """
        Guess the import mode of a file.

        At the moment this relies purely on the file extension.
        """
        try:
            filename = Graphs.tools_get_filename(settings.get_file())
            file_suffix = Path(filename).suffixes[-1]
        except IndexError:
            file_suffix = None
        for index, mode in enumerate(parsers.list_parsers()):
            suffixes = mode.get_file_suffixes()
            if suffixes is None:
                continue
            for suffix in suffixes:
                if file_suffix == suffix:
                    return index
        return 0  # columns

    @staticmethod
    def _on_init_import_settings_request(
        self,
        settings: Graphs.ImportSettings,
    ) -> None:
        """
        Init import settings.

        This is intended for filetypes, where the settings are dependent on
        the file itself or other runtime variables.
        """
        parser = parsers.get_parser(settings.get_mode())
        callback = parser.get_init_settings_function()
        if callback is not None:
            callback(settings)

    @staticmethod
    def _on_load_mode_settings_request(
        self,
        settings: Graphs.ImportSettings,
    ) -> Gtk.Widget:
        """Load the UI settings."""
        parser = parsers.get_parser(settings.get_mode())
        cls = parser.get_settings_widget_class()
        if cls is None:
            return None
        return cls.new(settings)

    @staticmethod
    def _on_import_request(
        self,
        itemlist: Gee.List,
        settings: Graphs.ImportSettings,
        data: Graphs.Data,
    ) -> str:
        parser = parsers.get_parser(settings.get_mode())
        callback = parser.get_import_function()
        style = data.get_selected_style_params()
        try:
            items = callback(settings, style)
            for item in items:
                Graphs.add_item_to_list(item, itemlist)
            return ""
        except ParseError as error:
            return error.message
        except Exception:
            message = _("Import failed")
            logging.exception(message)
            return message
