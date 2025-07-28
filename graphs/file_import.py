# SPDX-License-Identifier: GPL-3.0-or-later
"""
Module for importing data from files.

    Functions:
        import_from_files
"""
import logging
from gettext import gettext as _
from pathlib import Path

from gi.repository import Gee, Graphs

from graphs import parse_file
from graphs.misc import ParseError

_IMPORT_MODES = {
    # name: suffix
    "project": ".graphs",
    "xrdml": ".xrdml",
    "xry": ".xry",
    "columns": None,
}

_REQUESTS = (
    "guess_import_mode",
    "init_import_settings",
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

    @staticmethod
    def _on_guess_import_mode_request(
        self,
        settings: Graphs.ImportSettings,
    ) -> str:
        """
        Guess the import mode of a file.

        At the moment this relies purely on the file extension.
        """
        try:
            filename = Graphs.tools_get_filename(settings.get_file())
            file_suffix = Path(filename).suffixes[-1]
        except IndexError:
            file_suffix = None
        for mode, suffix in _IMPORT_MODES.items():
            if suffix is not None and file_suffix == suffix:
                return mode
        return "columns"

    @staticmethod
    def _on_init_import_settings_request(
        self,
        _settings: Graphs.ImportSettings,
    ) -> None:
        """
        Init import settings.

        This is intended for filetypes, where the settings are dependent on
        the file itself or other runtime variables.
        """

    @staticmethod
    def _on_import_request(
        self,
        itemlist: Gee.List,
        settings: Graphs.ImportSettings,
        data: Graphs.Data,
    ) -> str:
        callback = getattr(parse_file, "import_from_" + settings.get_mode())
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
