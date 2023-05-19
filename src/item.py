# SPDX-License-Identifier: GPL-3.0-or-later
import uuid

from matplotlib import pyplot


class ItemBase:
    def __init__(self, config, name="", color=None, selected=True):
        self.key: str = str(uuid.uuid4())
        self.name = name
        self.color = color
        self.selected = selected
        self.plot_y_position = config["plot_y_position"]
        self.plot_x_position = config["plot_x_position"]
        self.xlabel = ""
        self.ylabel = ""


class Item(ItemBase):
    def __init__(self, parent, xdata, ydata, name=""):
        config = parent.preferences.config
        super().__init__(config, name)
        self.xdata = xdata
        self.ydata = ydata
        self.linestyle = pyplot.rcParams["lines.linestyle"]
        self.linewidth = float(pyplot.rcParams["lines.linewidth"])
        self.markerstyle = pyplot.rcParams["lines.marker"]
        self.markersize = float(pyplot.rcParams["lines.markersize"])


class TextItem(ItemBase):
    def __init__(self, parent, x_anchor, y_anchor, text, name=""):
        config = parent.preferences.config
        super().__init__(config, name)
        self.x_anchor = x_anchor
        self.y_anchor = y_anchor
        self.text = text
