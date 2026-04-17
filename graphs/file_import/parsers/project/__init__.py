# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for "parsing" project files."""
from gettext import pgettext as C_

from gi.repository import Graphs

from graphs import project
from graphs.file_import.parsers import Parser
from graphs.item import ItemFactory
from graphs.misc import ParseError
from graphs.project import ProjectParseError


class ProjectParser(Parser):
    """Project parser."""

    __gtype_name__ = "GraphsProjectParser"

    def __init__(self):
        super().__init__(
            "project",
            C_("import-mode", "Project"),
            C_("file-filter", "Graphs Project File"),
            ["graphs"],
        )

    @staticmethod
    def parse(
        items: Graphs.ItemList,
        settings: Graphs.ImportSettings,
        _data: Graphs.Data,
    ) -> None:
        """Import data from project file."""
        try:
            project_dict = project.read_project_file(settings.get_file())
            items = list(map(ItemFactory.new_from_dict, project_dict["data"]))
            items.add_all(items)
        except ProjectParseError as e:
            raise ParseError(e.message) from e
