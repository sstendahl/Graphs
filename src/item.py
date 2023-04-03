# SPDX-License-Identifier: GPL-3.0-or-later
import uuid

from graphs import plotting_tools


class Item:
    def __init__(self, parent, xdata, ydata, name=""):
        config = parent.preferences.config
        style = parent.canvas.style
        self.key: str = str(uuid.uuid4())
        self.name = name
        self.plot_y_position = config["plot_y_position"]
        self.plot_x_position = config["plot_x_position"]
        self.selected = True
        self.color = plotting_tools.get_next_color(parent)
        self.xdata = xdata
        self.ydata = ydata
        self.clipboard_pos = -1
        self.xdata_clipboard = [self.xdata.copy()]
        self.ydata_clipboard = [self.ydata.copy()]
        self.linestyle = style["lines.linestyle"]
        self.linewidth = float(style["lines.linewidth"])
        self.markerstyle = style["lines.marker"]
        self.markersize = float(style["lines.markersize"])
