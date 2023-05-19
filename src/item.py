# SPDX-License-Identifier: GPL-3.0-or-later
import uuid

from matplotlib import pyplot


class ItemBase:
    def __init__(self, config, name="", color=None, selected=True):
        self.key: str = str(uuid.uuid4())
        self.name, self.color, self.selected = name, color, selected
        self.plot_y_position = config["plot_y_position"]
        self.plot_x_position = config["plot_x_position"]
        self.xlabel = ""
        self.ylabel = ""


class Item(ItemBase):
    def __init__(self, parent, xdata=None, ydata=None, name=""):
        config = parent.preferences.config
        super().__init__(config, name)
        if xdata is None:
            xdata = []
        if ydata is None:
            ydata = []
        self.xdata, self.ydata = xdata, ydata
        self.linestyle = pyplot.rcParams["lines.linestyle"]
        self.linewidth = float(pyplot.rcParams["lines.linewidth"])
        self.markerstyle = pyplot.rcParams["lines.marker"]
        self.markersize = float(pyplot.rcParams["lines.markersize"])


class TextItem(ItemBase):
    def __init__(self, parent, x_anchor, y_anchor, text, name=""):
        config = parent.preferences.config
        super().__init__(
            config, name=name, color=pyplot.rcParams["text.color"])
        self.x_anchor, self.y_anchor = float(x_anchor), float(y_anchor)
        self.text = text
        self.size = float(pyplot.rcParams["font.size"])
