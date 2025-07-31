# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing files."""
import logging

from . import (
    columns,
    project,
    xrdml,
    xry,
)


_IMPORT_MODES = {}


def _register_parser(
    name: str,
    import_function,
    file_suffixes: list[str],
    init_settings_function=None,
) -> None:
    """Register an import mode."""
    _IMPORT_MODES[name] = (
        import_function,
        file_suffixes,
        init_settings_function,
    )
    logging.debug("registered mode " + name)


def register_parsers():
    """Register all parsers."""
    _register_parser(
        "columns",
        columns.import_from_columns,
        None,
    )

    _register_parser(
        "project",
        project.import_from_project,
        [".graphs"],
    )

    _register_parser(
        "xrdml",
        xrdml.import_from_xrdml,
        [".xrdml"],
    )

    _register_parser(
        "xry",
        xry.import_from_xry,
        [".xry"],
    )


def list_modes() -> list[str]:
    """List all registered parse modes."""
    return list(_IMPORT_MODES.keys())


def get_import_function(mode: str):
    """Get the import function for a specific mode."""
    return _IMPORT_MODES[mode][0]


def get_suffixes(mode: str) -> list[str]:
    """Get file suffixes for a specific mode."""
    return _IMPORT_MODES[mode][1]


def get_init_settings_function(mode: str):
    """Get the init settings function for a specific mode."""
    return _IMPORT_MODES[mode][2]
