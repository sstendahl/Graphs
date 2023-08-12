# SPDX-License-Identifier: GPL-3.0-or-later
from enum import Enum


class InteractionMode(str, Enum):
    PAN = "pan/zoom"
    ZOOM = "zoom rect"
    SELECT = ""


class ParseError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


# Translatable lists
def _(message):
    return message


X_POSITIONS = [_("top"), _("bottom")]
Y_POSITIONS = [_("left"), _("right")]
LINESTYLES = [_("none"), _("solid"), _("dotted"), _("dashed"), _("dashdot")]
MARKERS = {
    _("Point"): ".", _("Pixel"): ",", _("Circle"): "o",
    _("Triangle down"): "v", _("Triangle up"): "^", _("Triangle left"): "<",
    _("Triangle right"): ">", _("Octagon"): "8", _("Square"): "s",
    _("Pentagon"): "p", _("Star"): "*", _("Hexagon 1"): "h",
    _("Hexagon 2"): "H", _("Plus"): "+", _("x"): "x", _("Diamond"): "D",
    _("Thin diamond"): "d", _("Vertical line"): "|", _("Horizontal line"): "_",
    _("Filled plus"): "P", _("Filled x"): "X", _("Nothing"): "none",
}
TICK_DIRECTIONS = [_("in"), _("out")]

del _
