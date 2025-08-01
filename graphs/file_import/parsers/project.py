# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for "parsing" project files."""
from gettext import pgettext as C_

from graphs import item, misc, project
from graphs.file_import.parsers import Parser
from graphs.misc import ParseError
from graphs.project import ProjectParseError


class ProjectParser(Parser):
    """Project parser."""

    __gtype_name__ = "GraphsProjectParser"

    def __init__(self):
        super().__init__(
            "project",
            C_("import-mode", "Project"),
            self.parse,
            [".graphs"],
        )

    @staticmethod
    def parse(params, _style) -> misc.ItemList:
        """Import data from project file."""
        try:
            project_dict = project.read_project_file(params.get_file())
            return list(map(item.new_from_dict, project_dict["data"]))
        except ProjectParseError as e:
            raise ParseError(e.message) from e
