# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import GObject, Graphs

from graphs import misc, utilities

from matplotlib import artist, pyplot
from matplotlib.figure import Figure


def new_for_item(canvas: Graphs.CanvasInterface, item: Graphs.Item):
    match item.__gtype_name__:
        case "GraphsDataItem":
            cls = DataItemArtistWrapper
        case "GraphsTextItem":
            cls = TextItemArtistWrapper
        case "GraphsFillItem":
            cls = FillItemArtistWrapper
        case _:
            pass
    artist_wrapper = cls(
        canvas.axes[item.get_yposition() * 2 + item.get_xposition()],
        item,
    )
    for prop in dir(artist_wrapper.props):
        if not (prop == "label" and artist_wrapper.legend):
            item.bind_property(prop, artist_wrapper, prop, 0)
    artist_wrapper.connect("notify", lambda _x, _y: canvas.update_legend())
    return artist_wrapper


class ItemArtistWrapper(GObject.Object):
    __gtype_name__ = "GraphsItemArtistWrapper"
    legend = False

    def get_artist(self) -> artist:
        return self._artist

    @GObject.Property(type=str, default="")
    def name(self) -> str:
        return self._artist.get_label()

    @name.setter
    def name(self, name: str) -> None:
        self._artist.set_label(utilities.shorten_label(name, 40))

    @GObject.Property(type=str, default="000000")
    def color(self) -> str:
        return self._artist.get_color()

    @color.setter
    def color(self, color: str) -> None:
        self._artist.set_color(color)

    @GObject.Property(type=float, default=1)
    def alpha(self) -> float:
        return self._artist.get_alpha()

    @alpha.setter
    def alpha(self, alpha: float) -> None:
        self._artist.set_alpha(alpha)


class DataItemArtistWrapper(ItemArtistWrapper):
    __gtype_name__ = "GraphsDataItemArtistWrapper"
    selected = GObject.Property(type=bool, default=True)
    linewidth = GObject.Property(type=float, default=3)
    markersize = GObject.Property(type=float, default=7)
    legend = True

    @GObject.Property
    def xdata(self) -> list:
        return self._artist.get_xdata()

    @xdata.setter
    def xdata(self, xdata: list) -> None:
        self._artist.set_xdata(xdata)

    @GObject.Property
    def ydata(self) -> list:
        return self._artist.get_ydata()

    @ydata.setter
    def ydata(self, ydata: list) -> None:
        self._artist.set_ydata(ydata)

    @GObject.Property(type=int, default=1)
    def linestyle(self) -> int:
        return misc.LINESTYLES.index(self._artist.get_linestyle())

    @linestyle.setter
    def linestyle(self, linestyle: int) -> None:
        self._artist.set_linestyle(misc.LINESTYLES[linestyle])

    @GObject.Property(type=int, default=1)
    def markerstyle(self) -> int:
        return misc.MARKERSTYLES.index(self._artist.get_marker())

    @markerstyle.setter
    def markerstyle(self, markerstyle: int) -> None:
        self._artist.set_marker(misc.MARKERSTYLES[markerstyle])

    def _set_properties(self, _x, _y) -> None:
        linewidth, markersize = self.props.linewidth, self.props.markersize
        if not self.props.selected:
            linewidth *= 0.35
            markersize *= 0.35
        self._artist.set_linewidth(linewidth)
        self._artist.set_markersize(markersize)

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        super().__init__()
        self._artist = axis.plot(
            item.props.xdata,
            item.props.ydata,
            label=utilities.shorten_label(item.get_name(), 40),
            color=item.get_color(),
            alpha=item.get_alpha(),
            linestyle=misc.LINESTYLES[item.props.linestyle],
            marker=misc.MARKERSTYLES[item.props.markerstyle],
        )[0]
        for prop in ("selected", "linewidth", "markersize"):
            self.set_property(prop, item.get_property(prop))
            self.connect(f"notify::{prop}", self._set_properties)
        self._set_properties(None, None)


class TextItemArtistWrapper(ItemArtistWrapper):
    __gtype_name__ = "GraphsTextItemArtistWrapper"

    @GObject.Property(type=float, default=12)
    def size(self) -> float:
        return self._artist.get_fontsize()

    @size.setter
    def size(self, size: float) -> None:
        self._artist.set_fontsize(size)

    @GObject.Property(type=int, default=0, minimum=0, maximum=360)
    def rotation(self) -> int:
        return self._artist.get_rotation()

    @rotation.setter
    def rotation(self, rotation: int) -> None:
        self._artist.set_rotation(rotation)

    @GObject.Property(type=str, default="")
    def text(self) -> str:
        return self._artist.get_text()

    @text.setter
    def text(self, text: str) -> None:
        self._artist.set_text(text)

    @GObject.Property(type=float, default=0)
    def xanchor(self) -> float:
        return self._artist.get_position()[0]

    @xanchor.setter
    def xanchor(self, xanchor: float) -> None:
        self._artist.set_position((xanchor, self.props.yanchor))

    @GObject.Property(type=float, default=0)
    def yanchor(self) -> float:
        return self._artist.get_position()[1]

    @yanchor.setter
    def yanchor(self, yanchor: float) -> None:
        self._artist.set_position((self.props.xanchor, yanchor))

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        super().__init__()
        self._artist = axis.text(
            item.props.xanchor,
            item.props.yanchor,
            item.props.text,
            label=utilities.shorten_label(item.get_name(), 40),
            color=item.get_color(),
            alpha=item.get_alpha(),
            clip_on=True,
            fontsize=item.props.size,
            rotation=item.props.rotation,
        )


class FillItemArtistWrapper(ItemArtistWrapper):
    __gtype_name__ = "GraphsFillItemArtistWrapper"

    @GObject.Property(type=object, flags=2)
    def data(self) -> None:
        pass

    @data.setter
    def data(self, data) -> None:
        dummy = Figure().add_subplot().fill_between(*data)
        self._artist.set_paths([dummy.get_paths()[0].vertices])

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        super().__init__()
        self._artist = axis.fill_between(
            *item.props.data,
            label=utilities.shorten_label(item.get_name(), 40),
            color=item.get_color(),
            alpha=item.get_alpha(),
        )
