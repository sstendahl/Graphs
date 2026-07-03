# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for importing data from files."""
import logging
from gettext import gettext as _

from gi.repository import Graphs, Gtk

from graphs.misc import ParseError


class Parser(Graphs.PythonParser):
    """Python Parser base class."""

    __gtype_name__ = "GraphsPythonParserBase"

    _REQUESTS = (
        "init_import_settings",
        "append_settings_widgets",
        "parse",
    )

    def __init__(
        self,
        name: str,
        ui_name: str,
        filetype_name: str,
        file_suffixes: list[str],
    ):
        super().__init__(
            name=name,
            ui_name=ui_name,
            filetype_name=filetype_name,
            file_suffixes=file_suffixes,
        )

        for request in self._REQUESTS:
            request = request + "-request"
            self.connect(
                request,
                getattr(self, "_on_" + request.replace("-", "_")),
            )

    @staticmethod
    def _on_init_import_settings_request(
        self,
        settings: Graphs.ImportSettings,
    ) -> str:
        """
        Init import settings.

        This is intended for filetypes, where the settings are dependent on
        the file itself or other runtime variables.
        """
        try:
            return self.init_settings(settings)
        except Exception:
            message = _("parser failed to init settings.")
            logging.exception(message)
            return message

    @staticmethod
    def _on_append_settings_widgets_request(
        self,
        settings: Graphs.ImportSettings,
        settings_box: Gtk.Box,
    ) -> str:
        """Load the UI settings."""
        try:
            self.init_settings_widgets(settings, settings_box)
            return ""
        except Exception:
            message = _("parser failed to init settings widgets.")
            logging.exception(message)
            return message

    @staticmethod
    def _on_parse_request(
        self,
        itemlist: Graphs.ItemList,
        settings: Graphs.ImportSettings,
        style: Graphs.StyleParameters,
    ) -> str:
        try:
            self.parse(itemlist, settings, style)
            return ""
        except ParseError as error:
            return error.message
        except Exception:
            message = _("Import failed")
            logging.exception(message)
            return message

    @staticmethod
    def parse(_items, _settings, _style) -> str:
        """
        Parse a file given params.

        Must be implemented by parsers.
        """
        raise NotImplementedError

    @staticmethod
    def init_settings(_settings) -> str:
        """Init settings."""
        return ""

    @staticmethod
    def init_settings_widgets(_settings, _box) -> str:
        """Create settings widgets and append them to box."""
        return ""
