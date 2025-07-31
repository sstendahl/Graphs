# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing files."""
import logging
from gettext import pgettext as C_

from gi.repository import Graphs

from . import (
    columns,
    project,
    xrdml,
    xry,
)


_PARSERS = []


class Parser(Graphs.Parser):
    """Parser class."""

    def __init__(
        self,
        name: str,
        ui_name: str,
        import_function,
        file_suffixes: list[str],
        init_settings_function=None,
    ):
        super().__init__(name=name, ui_name=ui_name)
        self._import_function = import_function
        self._file_suffixes = file_suffixes
        self._init_settings_function = init_settings_function

    def get_import_function(self):
        """Get import function."""
        return self._import_function

    def get_file_suffixes(self):
        """Get file suffixes."""
        return self._file_suffixes

    def get_init_settings_function(self):
        """Get init settings function."""
        return self._init_settings_function


def _register_parser(
    name: str,
    ui_name: str,
    import_function,
    file_suffixes: list[str],
    init_settings_function=None,
) -> None:
    """Register an import mode."""
    _PARSERS.append(Parser(
        name,
        ui_name,
        import_function,
        file_suffixes,
        init_settings_function,
    ))
    logging.debug("registered mode " + name)


def register_parsers():
    """Register all parsers."""
    _register_parser(
        "columns",
        C_("import-mode", "Columns"),
        columns.import_from_columns,
        None,
    )

    _register_parser(
        "project",
        C_("import-mode", "Project"),
        project.import_from_project,
        [".graphs"],
    )

    _register_parser(
        "xrdml",
        C_("import-mode", "xrdml"),
        xrdml.import_from_xrdml,
        [".xrdml"],
    )

    _register_parser(
        "xry",
        C_("import-mode", "xry"),
        xry.import_from_xry,
        [".xry"],
    )


def list_parsers() -> list[Parser]:
    """List all registered parse modes."""
    return _PARSERS


def list_parser_names() -> list[str]:
    """List all localised parse names."""
    return [parser[0] for parser in _PARSERS]


def get_parser(index: int) -> Parser:
    """Get parser."""
    return _PARSERS[index]
