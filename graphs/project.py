# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for saving and loading projects."""
from gi.repository import Gio

from graphs import file_io, migrate


def read_project_file(file: Gio.File) -> dict:
    """Read a project dict from file and account for migration."""
    try:
        project_dict = file_io.parse_json(file)
    except UnicodeDecodeError:
        project_dict = migrate.migrate_project(file)
    return project_dict


def save_project_dict(file: Gio.File, project_dict: dict) -> None:
    """Save a project dict to a file."""
    file_io.write_json(file, project_dict)
