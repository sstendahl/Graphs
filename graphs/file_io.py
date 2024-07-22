# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for file operations."""
import json
from xml.dom import minidom

from gi.repository import Gio

import gio_pyio


def create_write_stream(file: Gio.File) -> Gio.OutputStream:
    """Create a write stream for a given file."""
    if file.query_exists(None):
        file.delete(None)
    return file.create(0, None)


def iter_data_stream(stream: Gio.DataInputStream):
    """
    Iterate over a data stream.

    Note: This can be removed in the next release of pygobject.
    """
    line = stream.read_line_utf8(None)[0]
    while line is not None:
        yield line
        line = stream.read_line_utf8(None)[0]


def parse_json(file: Gio.File) -> dict:
    """Parse a json file to a python dict."""
    with gio_pyio.open(file, "rb") as wrapper:
        return json.load(wrapper)


def write_json(file: Gio.File, json_object: dict, pretty_print=True) -> None:
    """Write a python dict to a python file."""
    with gio_pyio.open(file, "wt") as wrapper:
        json.dump(
            json_object,
            wrapper,
            indent=4 if pretty_print else None,
            sort_keys=True,
        )


def parse_xml(file: Gio.File) -> dict:
    """Parse a xml file to a python dict."""
    with gio_pyio.open(file, "rb") as wrapper:
        return minidom.parse(wrapper)
