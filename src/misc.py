# SPDX-License-Identifier: GPL-3.0-or-later
from enum import Enum


class ImportSettings():
    def __init__(self, config, name="", path="", params=None):
        self.name = name
        self.path = path
        if params is None:
            params = {
                "delimiter": config["import_delimiter"],
                "guess_headers": config["guess_headers"],
                "separator": config["import_separator"],
                "skip_rows": config["import_skip_rows"],
                "column_x": config["import_column_x"],
                "column_y": config["import_column_y"],
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
        self.custom_plot_style = config["plot_custom_style"]


class ImportMode(Enum):
    SINGLE = 1
    MULTIPLE = 2


class InteractionMode(Enum):
    PAN = 1
    ZOOM = 2
    SELECT = 3
