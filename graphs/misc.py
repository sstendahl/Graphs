# SPDX-License-Identifier: GPL-3.0-or-later
"""Miscallaneous constants."""
import sympy


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


X = sympy.Symbol("x")

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
