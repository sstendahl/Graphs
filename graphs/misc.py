# SPDX-License-Identifier: GPL-3.0-or-later
"""Miscallaneous constants."""
import enum

from gi.repository import Graphs

# Type hints
ItemList = list[Graphs.Item]
Limits = tuple[float, float, float, float]


class ParseError(Exception):
    """Custom Error for parsing files."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InvalidEquationError(Exception):
    """Custom Error for invalid equation."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ChangeType(enum.Enum):
    """Enum for handling changetypes."""

    ITEM_PROPERTY_CHANGED = 0
    ITEM_ADDED = 1
    ITEM_REMOVED = 2
    ITEMS_SWAPPED = 3
    FIGURE_SETTINGS_CHANGED = 4


LEGEND_POSITIONS = [
    "best",
    "upper right",
    "upper left",
    "lower left",
    "lower right",
    "center left",
    "center right",
    "lower center",
    "upper center",
    "center",
]
DELIMITERS = {
    "whitespace": "\\s+",
    "tab": "\\t+",
    "colon": ":",
    "semicolon": ";",
    "comma": ",",
    "period": ".",
    "custom": "custom",
}
SEPARATORS = {
    "comma": ",",
    "period": ".",
}
LINESTYLES = ["none", "solid", "dotted", "dashed", "dashdot"]
MARKERSTYLES = [
    "none",
    ".",
    ",",
    "o",
    "v",
    "^",
    "<",
    ">",
    "8",
    "s",
    "p",
    "*",
    "h",
    "H",
    "+",
    "x",
    "D",
    "d",
    "|",
    "_",
    "P",
    "X",
]

DIRECTIONS = ["bottom", "top", "left", "right"]

LIMITS = [
    f"{prefix}-{direction}" for direction in DIRECTIONS
    for prefix in ("min", "max")
]
