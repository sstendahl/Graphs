# SPDX-License-Identifier: GPL-3.0-or-later
from enum import Enum


class PlotSettings:
    """
    The plot-related settings for the current session. The default values are
    retreived from the config file through preferences.
    """
    def __init__(self, config):
        self.xlabel = config["plot_x_label"]
        self.right_label = config["plot_right_label"]
        self.top_label = config["plot_top_label"]
        self.ylabel = config["plot_y_label"]
        self.xscale = config["plot_x_scale"]
        self.yscale = config["plot_y_scale"]
        self.right_scale = config["plot_right_scale"]
        self.top_scale = config["plot_top_scale"]
        self.title = config["plot_title"]
        self.legend = config["plot_legend"]
        self.use_custom_plot_style = config["plot_use_custom_style"]
        self.legend_position = config["plot_legend_position"]
        self.custom_plot_style = config["plot_custom_style"]


class InteractionMode(Enum):
    PAN = 1
    ZOOM = 2
    SELECT = 3


# Translatable lists
def _(message):
    return message


SCALES = [_("linear"), _("log")]
LEGEND_POSITIONS = [
    _("Best"), _("Upper right"), _("Upper left"), _("Lower left"),
    _("Lower right"), _("Center left"), _("Center right"), _("Lower center"),
    _("Upper center"), _("Center"),
]
X_POSITIONS = [_("top"), _("bottom")]
Y_POSITIONS = [_("left"), _("right")]
SEPARATORS = [",", "."]
ACTION_CENTER_DATA = [
    _("Center at maximum Y value"), _("Center at middle coordinate"),
]
HANDLE_DUPLICATES = [
    _("Auto-rename duplicates"), _("Ignore duplicates"), _("Add duplicates"),
    _("Override existing items"),
]
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
