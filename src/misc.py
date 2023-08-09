# SPDX-License-Identifier: GPL-3.0-or-later
from enum import Enum


def _get_scale(settings, key):
    return "linear" if settings.get_enum(key) == 0 else "log"


class PlotSettings:
    """
    The plot-related settings for the current session. The default values are
    retreived from the preferencess file.
    """
    def __init__(self, settings):
        self.xlabel = None
        self.right_label = None
        self.top_label = None
        self.ylabel = None
        self.xscale = _get_scale(settings, "bottom-scale")
        self.yscale = _get_scale(settings, "left-scale")
        self.right_scale = _get_scale(settings, "right-scale")
        self.top_scale = _get_scale(settings, "top-scale")
        self.title = settings.get_string("title")
        self.legend = settings.get_boolean("legend")
        self.use_custom_plot_style = settings.get_boolean("use-custom-style")
        self.legend_position = settings.get_string("legend-position")
        self.custom_plot_style = settings.get_string("custom-style")
        self.min_bottom = 0
        self.max_bottom = 1
        self.min_top = 0
        self.max_top = 10
        self.min_left = 0
        self.max_left = 1
        self.min_right = 0
        self.max_right = 10


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
