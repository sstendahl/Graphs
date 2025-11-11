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
        filetype_name: str,
        file_suffixes: list[str],
    ):
        super().__init__(
            name=name,
            ui_name=ui_name,
            filetype_name=filetype_name,
            file_suffixes=file_suffixes,
        )

    @staticmethod
    def parse(_settings, _style) -> None:
        """
        Parse a file given params.

        Must be implemented by parsers.
        """
        raise NotImplementedError

    @staticmethod
    def init_settings(_settings) -> bool:
        """Init settings."""
        return True

    @staticmethod
    def init_settings_widgets(_settings, _box) -> None:
        """Create settings widgets and append them to box."""


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
