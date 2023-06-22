# SPDX-License-Identifier: GPL-3.0-or-later
import uuid

from matplotlib import pyplot


class ItemBase:
    def __init__(self, preferences, name="", color=None, selected=True,
                 xlabel="", ylabel=""):
        self.key: str = str(uuid.uuid4())
        self.name, self.color, self.selected = name, color, selected
        self.xlabel, self.ylabel = xlabel, ylabel
        self.plot_y_position = preferences["plot_y_position"]
        self.plot_x_position = preferences["plot_x_position"]
        self.alpha = 1


class Item(ItemBase):
    def __init__(self, application, xdata=None, ydata=None, name="",
                 xlabel="", ylabel=""):
        super().__init__(
            application.preferences, name=name, xlabel=xlabel, ylabel=ylabel)
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
    def __init__(self, application, x_anchor=0, y_anchor=0, text="", name=""):
        super().__init__(
            application.preferences, name=name,
            color=pyplot.rcParams["text.color"])
        self.x_anchor, self.y_anchor = float(x_anchor), float(y_anchor)
        self.text = text
        self.size = float(pyplot.rcParams["font.size"])
        self.rotation = 0
