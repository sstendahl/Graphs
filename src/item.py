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
        params = pyplot.rcParams
        figure_settings = application.get_data().get_figure_settings()
        return DataItem(
            xposition=figure_settings.get_x_position(),
            yposition=figure_settings.get_y_position(),
            linestyle=misc.LINESTYLES.index(params["lines.linestyle"]),
            linewidth=params["lines.linewidth"],
            markerstyle=misc.MARKERSTYLES.index(params["lines.marker"]),
            markersize=params["lines.markersize"],
            xdata=xdata, ydata=ydata, **kwargs,
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.props.xdata is None:
            self.props.xdata = []
        if self.props.ydata is None:
            self.props.ydata = []

    def reset(self):
        params = pyplot.rcParams
        self.props.linestyle = misc.LINESTYLES.index(params["lines.linestyle"])
        self.props.linewidth = params["lines.linewidth"]
        self.props.markerstyle = \
            misc.MARKERSTYLES.index(params["lines.marker"])
        self.props.markersize = params["lines.markersize"]
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
        params = pyplot.rcParams
        figure_settings = application.get_data().get_figure_settings()
        return TextItem(
            xposition=figure_settings.get_x_position(),
            yposition=figure_settings.get_y_position(),
            size=params["font.size"], color=params["text.color"],
            xanchor=xanchor, yanchor=yanchor, text=text, **kwargs,
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def reset(self):
        params = pyplot.rcParams
        self.props.size = params["font.size"]
        self.props.color = params["text.color"]
