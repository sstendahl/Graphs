# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for file operations."""
import json
from xml.dom import minidom

from gi.repository import Gio

import gio_pyio


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
