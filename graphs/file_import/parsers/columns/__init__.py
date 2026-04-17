# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing columns files."""
from gettext import pgettext as C_

from gi.repository import GLib, Graphs

from graphs.file_import.parsers import Parser
from graphs.misc import ParseError


class ColumnsParser(Parser):
    """Columns parser."""

    def __init__(self):
        super().__init__(
            "columns",
            C_("import-mode", "Columns"),
            None,
            None,
        )

    @staticmethod
    def parse(
        items: Graphs.ItemList,
        settings: Graphs.ImportSettings,
        data: Graphs.Data,
    ) -> None:
        """Import data from columns file."""
        parser = Graphs.ColumnsParser.new(settings)

        try:
            parser.parse()
            parser.add_items(data, items)
        except GLib.Error as e:
            raise ParseError(e.message) from e

    @staticmethod
    def init_settings_widgets(settings, box) -> None:
        """Append columns specific settings."""
        box.append(Graphs.ColumnsBox.new(settings))
