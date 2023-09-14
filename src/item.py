# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import GObject, Graphs

from graphs import misc

from matplotlib import pyplot


def new_from_dict(dictionary: dict):
    match dictionary["type"]:
        case "GraphsDataItem":
            cls = DataItem
        case "GrapsTextItem":
            cls = TextItem
        case _:
            pass
    dictionary.pop("type")
    return cls(**dictionary)


def to_dict(item):
    dictionary = {key: item.get_property(key) for key in dir(item.props)}
    dictionary["type"] = item.__gtype_name__
    return dictionary


class DataItem(Graphs.Item):
    __gtype_name__ = "GraphsDataItem"

    xdata = GObject.Property(type=object)
    ydata = GObject.Property(type=object)
    linestyle = GObject.Property(type=int, default=1)
    linewidth = GObject.Property(type=float, default=3)
    markerstyle = GObject.Property(type=int, default=0)
    markersize = GObject.Property(type=float, default=7)

    @staticmethod
    def new(application, xdata=None, ydata=None, **kwargs):
        settings = application.get_settings("general")
        return DataItem(
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


class TextItem(Graphs.Item):
    __gtype_name__ = "GraphsTextItem"

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
