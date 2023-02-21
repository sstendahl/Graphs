# SPDX-License-Identifier: GPL-3.0-or-later
from enum import Enum

from matplotlib.backend_bases import NavigationToolbar2


class ImportSettings():
    def __init__(self, parent):
        cfg = parent.preferences.config
        self.name = ""
        self.path = ""
        self.delimiter = cfg["import_delimiter"]
        self.guess_headers = cfg["guess_headers"]
        self.separator = cfg["import_separator"]
        self.skip_rows = cfg["import_skip_rows"]
        self.column_x = cfg["import_column_x"]
        self.column_y = cfg["import_column_y"]


class ImportMode(Enum):
    SINGLE = 1
    MULTIPLE = 2


class InteractionMode(Enum):
    PAN = 1
    ZOOM = 2
    SELECT = 3


class DummyToolbar(NavigationToolbar2):
    """Own implementation of NavigationToolbar2 for rubberband support."""
    def draw_rubberband(self, _event, x_0, y_0, x_1, y_1):
        self.canvas._rubberband_rect = [int(val) for val in (x_0,
                                        self.canvas.figure.bbox.height - y_0,
                                        x_1 - x_0, y_0 - y_1)]
        self.canvas.queue_draw()

    def remove_rubberband(self):
        self.canvas._rubberband_rect = None
        self.canvas.queue_draw()
