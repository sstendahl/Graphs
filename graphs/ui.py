# SPDX-License-Identifier: GPL-3.0-or-later
"""Some UI utilities."""
from gi.repository import Gtk

from graphs import utilities


def validate_entry(entry: Gtk.Editable) -> float:
    """Validate an entry for having a parsable bool value."""
    value = utilities.string_to_float(entry.get_text())
    is_valid = value is not None
    if is_valid:
        entry.remove_css_class("error")
    else:
        entry.add_css_class("error")
    return is_valid, value
