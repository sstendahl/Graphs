# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for "parsing" project files."""
from graphs import item, misc, project
from graphs.misc import ParseError
from graphs.project import ProjectParseError


def import_from_project(params, _style) -> misc.ItemList:
    """Import data from project file."""
    try:
        project_dict = project.read_project_file(params.get_file())
        return list(map(item.new_from_dict, project_dict["data"]))
    except ProjectParseError as e:
        raise ParseError(e.message) from e
