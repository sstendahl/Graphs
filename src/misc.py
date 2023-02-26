# SPDX-License-Identifier: GPL-3.0-or-later
from enum import Enum

class ImportSettings():
    def __init__(self, parent, name="", path="", params=None):
        self.name = name
        self.path = path
        if params is None:
            cfg = parent.preferences.config
            params = {
                "delimiter": cfg["import_delimiter"],
                "guess_headers": cfg["guess_headers"],
                "separator": cfg["import_separator"],
                "skip_rows": cfg["import_skip_rows"],
                "column_x": cfg["import_column_x"],
                "column_y": cfg["import_column_y"]
            }
        self.delimiter = params["delimiter"]
        self.guess_headers = params["guess_headers"]
        self.separator = params["separator"]
        self.skip_rows = params["skip_rows"]
        self.column_x = params["column_x"]
        self.column_y = params["column_y"]


class PlotSettings:
    """
    The plot-related settings for the current session. The default values are
    retreived from the config file through preferences.
    """
    def __init__(self, config):
        self.font_string = config["plot_font_string"]
        self.xlabel = config["plot_X_label"]
        self.right_label = config["plot_right_label"]
        self.top_label = config["plot_top_label"]
        self.ylabel = config["plot_Y_label"]
        self.xscale = config["plot_X_scale"]
        self.yscale = config["plot_Y_scale"]
        self.right_scale = config["plot_right_scale"]
        self.top_scale = config["plot_top_scale"]
        self.title = config["plot_title"]
        self.font_weight = config["plot_font_weight"]
        self.font_family = config["plot_font_family"]
        self.font_size = config["plot_font_size"]
        self.font_style = config["plot_font_style"]
        self.tick_direction = config["plot_tick_direction"]
        self.major_tick_length = config["plot_major_tick_length"]
        self.minor_tick_length = config["plot_minor_tick_length"]
        self.major_tick_width = config["plot_major_tick_width"]
        self.minor_tick_width = config["plot_minor_tick_width"]
        self.tick_top = config["plot_tick_top"]
        self.tick_bottom = config["plot_tick_bottom"]
        self.tick_left = config["plot_tick_left"]
        self.tick_right = config["plot_tick_right"]
        self.legend = config["plot_legend"]


class ImportMode(Enum):
    SINGLE = 1
    MULTIPLE = 2


class InteractionMode(Enum):
    PAN = 1
    ZOOM = 2
    SELECT = 3
