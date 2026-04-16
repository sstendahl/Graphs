# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing xry files."""
from gettext import pgettext as C_

from gi.repository import Graphs

from graphs.file_import.parsers import Parser


class XryParser(Parser):
    """Xry parser."""

    __gtype_name__ = "GraphsPythonXryParser"

    def __init__(self):
        super().__init__(
            "xry",
            C_("import-mode", "xry"),
            C_("file-filter", "Leybold xry"),
            ["xry"],
        )

    @staticmethod
    def parse(
        items: Graphs.ItemList,
        settings: Graphs.ImportSettings,
        data: Graphs.Data,
    ) -> None:
        """Import data from .xry files used by Leybold X-ray apparatus."""
        parser = Graphs.XryParser.new()
        parser.parse(data, settings, items)
