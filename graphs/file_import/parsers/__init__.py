# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing files."""
import logging

from gi.repository import Graphs

_PARSERS = []


class Parser(Graphs.Parser):
    """Parser class."""

    __gtype_name__ = "GraphsPythonParser"

    def __init__(
        self,
        name: str,
        ui_name: str,
        parse_function,
        file_suffixes: list[str],
        settings_widgets_function=None,
        init_settings_function=None,
    ):
        super().__init__(name=name, ui_name=ui_name)
        self._parse_function = parse_function
        self._file_suffixes = file_suffixes
        self._settings_widgets_function = settings_widgets_function
        self._init_settings_function = init_settings_function

    def get_parse_function(self):
        """Get import function."""
        return self._parse_function

    def get_file_suffixes(self):
        """Get file suffixes."""
        return self._file_suffixes

    def get_settings_widgets_function(self):
        """Get settings widget function."""
        return self._settings_widgets_function

    def get_init_settings_function(self):
        """Get init settings function."""
        return self._init_settings_function


def register_parser(parser: Parser) -> None:
    """Register an import mode."""
    _PARSERS.append(parser)
    logging.debug("registered mode " + parser.get_name())


def list_parsers() -> list[Parser]:
    """List all registered parse modes."""
    return _PARSERS


def list_parser_names() -> list[str]:
    """List all localised parse names."""
    return [parser[0] for parser in _PARSERS]


def get_parser(index: int) -> Parser:
    """Get parser."""
    return _PARSERS[index]
