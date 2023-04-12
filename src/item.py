# SPDX-License-Identifier: GPL-3.0-or-later
import uuid

from graphs import plotting_tools

from matplotlib import pyplot


class Item:
    def __init__(self, parent, xdata, ydata, name=""):
        config = parent.preferences.config
        self.key: str = str(uuid.uuid4())
        self.name = name
        self.plot_y_position = config["plot_y_position"]
        self.plot_x_position = config["plot_x_position"]
        self.selected = True
        self.color = plotting_tools.get_next_color(parent)
        self.xdata = xdata
        self.ydata = ydata
        self.linestyle = pyplot.rcParams["lines.linestyle"]
        self.linewidth = float(pyplot.rcParams["lines.linewidth"])
        self.markerstyle = pyplot.rcParams["lines.marker"]
        self.markersize = float(pyplot.rcParams["lines.markersize"])
