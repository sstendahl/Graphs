# SPDX-License-Identifier: GPL-3.0-or-later
import uuid

from gi.repository import GObject, Graphs

from graphs import misc, utilities

from matplotlib import pyplot


def new_from_dict(dictionary: dict):
    match dictionary["item_type"]:
        case "Item":
            cls = Item
        case "TextItem":
            cls = TextItem
        case _:
            pass
    return cls(**dictionary)


class ItemBase(GObject.Object, Graphs.ItemRenderable, Graphs.Item):
    __gtype_name__ = "ItemBase"

    name = GObject.Property(type=str, default="")
    color = GObject.Property(type=str, default="")
    selected = GObject.Property(type=bool, default=True)
    xlabel = GObject.Property(type=str, default="")
    ylabel = GObject.Property(type=str, default="")
    xposition = GObject.Property(type=int, default=0)
    yposition = GObject.Property(type=int, default=0)
    alpha = GObject.Property(type=float, default=1, minimum=0, maximum=1)

    key = GObject.Property(type=str, default="")
    item_type = GObject.Property(type=str, default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.props.key == "":
            self.props.key = str(uuid.uuid4())
        if self.props.item_type == "":
            self.props.item_type = self.__gtype_name__

    def to_dict(self) -> dict:
        return {key: self.get_property(key) for key in dir(self.props)}

    def get_color(self):
        rgba = utilities.hex_to_rgba(self.props.color)
        rgba.alpha = self.props.alpha
        return rgba

    def set_color(self, rgba):
        self.props.alpha = rgba.alpha
        self.props.color = utilities.rgba_to_hex(rgba)


class Item(ItemBase):
    __gtype_name__ = "Item"

    xdata = GObject.Property(type=object)
    ydata = GObject.Property(type=object)
    linestyle = GObject.Property(type=int, default=1)
    linewidth = GObject.Property(type=float, default=3)
    markerstyle = GObject.Property(type=int, default=0)
    markersize = GObject.Property(type=float, default=7)

    @staticmethod
    def new(application, xdata=None, ydata=None, **kwargs):
        settings = application.get_settings("general")
        return Item(
            yposition=settings.get_enum("y-position"),
            xposition=settings.get_enum("x-position"),
            linestyle=misc.LINESTYLES.index(
                pyplot.rcParams["lines.linestyle"],
            ),
            linewidth=pyplot.rcParams["lines.linewidth"],
            markerstyle=misc.MARKERSTYLES.index(
                pyplot.rcParams["lines.marker"],
            ),
            markersize=pyplot.rcParams["lines.markersize"],
            xdata=xdata, ydata=ydata, **kwargs,
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.props.xdata is None:
            self.props.xdata = []
        if self.props.ydata is None:
            self.props.ydata = []

    def reset(self):
        self.props.linestyle = \
            misc.LINESTYLES.index(pyplot.rcParams["lines.linestyle"])
        self.props.linewidth = pyplot.rcParams["lines.linewidth"]
        self.props.markerstyle = \
            misc.MARKERSTYLES.index(pyplot.rcParams["lines.marker"])
        self.props.markersize = pyplot.rcParams["lines.markersize"]
        self.color = "000000"


class TextItem(ItemBase):
    __gtype_name__ = "TextItem"

    xanchor = GObject.Property(type=float, default=0)
    yanchor = GObject.Property(type=float, default=0)
    text = GObject.Property(type=str, default="")
    size = GObject.Property(type=float, default=12)
    rotation = GObject.Property(type=int, default=0, minimum=0, maximum=360)

    @staticmethod
    def new(application, xanchor=0, yanchor=0, text="", **kwargs):
        settings = application.get_settings("general")
        return TextItem(
            yposition=settings.get_enum("y-position"),
            xposition=settings.get_enum("x-position"),
            size=pyplot.rcParams["font.size"],
            xanchor=xanchor, yanchor=yanchor, text=text, **kwargs,
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.props.color == "":
            self.props.color = pyplot.rcParams["text.color"]

    def reset(self):
        self.props.size = pyplot.rcParams["font.size"]
        self.props.color = pyplot.rcParams["text.color"]
