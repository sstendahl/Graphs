# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import GObject, Graphs

from graphs import misc, utilities


def new_for_item(canvas, item):
    match item.props.item_type:
        case "Item":
            cls = ItemArtistWrapper
        case "TextItem":
            cls = TextItemArtistWrapper
        case _:
            pass
    artist = cls(canvas.axes[item.yposition * 2 + item.xposition], item)
    for prop in dir(artist.props):
        if not (prop == "label" and artist.legend):
            item.bind_property(prop, artist, prop, 0)
    artist.connect("notify", lambda _x, _y: canvas.update_legend())
    return artist


class ArtistWrapperBase(GObject.Object):
    __gtype_name__ = "ArtistWrapperBase"
    legend = False

    def get_artist(self):
        return self._artist

    @GObject.Property(type=str, default="")
    def name(self) -> str:
        return self._artist.get_label()

    @name.setter
    def name(self, name: str):
        self._artist.set_label(utilities.shorten_label(name, 40))

    @GObject.Property(type=str, default="000000")
    def color(self) -> str:
        return self._artist.get_color()

    @color.setter
    def color(self, color: str):
        self._artist.set_color(color)

    @GObject.Property(type=float, default=1)
    def alpha(self) -> float:
        return self._artist.get_alpha()

    @alpha.setter
    def alpha(self, alpha: float):
        self._artist.set_alpha(alpha)


class ItemArtistWrapper(ArtistWrapperBase):
    __gtype_name__ = "ItemArtistWrapper"
    selected = GObject.Property(type=bool, default=True)
    linewidth = GObject.Property(type=float, default=3)
    markersize = GObject.Property(type=float, default=7)
    legend = True

    @GObject.Property
    def xdata(self) -> list:
        return self._artist.get_xdata()

    @xdata.setter
    def xdata(self, xdata: list):
        self._artist.set_xdata(xdata)

    @GObject.Property
    def ydata(self) -> list:
        return self._artist.get_ydata()

    @ydata.setter
    def ydata(self, ydata: list):
        self._artist.set_ydata(ydata)

    @GObject.Property(type=int, default=1)
    def linestyle(self) -> int:
        return misc.LINESTYLES.index(self._artist.get_linestyle())

    @linestyle.setter
    def linestyle(self, linestyle: int):
        self._artist.set_linestyle(misc.LINESTYLES[linestyle])

    @GObject.Property(type=int, default=1)
    def markerstyle(self) -> int:
        return misc.MARKERSTYLES.index(self._artist.get_marker())

    @markerstyle.setter
    def markerstyle(self, markerstyle: int):
        self._artist.set_marker(misc.MARKERSTYLES[markerstyle])

    def _set_properties(self, _x, _y):
        linewidth, markersize = self.props.linewidth, self.props.markersize
        if not self.props.selected:
            linewidth *= 0.35
            markersize *= 0.35
        self._artist.set_linewidth(linewidth)
        self._artist.set_markersize(markersize)

    def __init__(self, axis, item):
        super().__init__()
        self._artist = axis.plot(
            item.props.xdata, item.props.ydata,
            label=utilities.shorten_label(item.props.name, 40),
            color=item.props.color, alpha=item.props.alpha,
            linestyle=misc.LINESTYLES[item.props.linestyle],
            marker=misc.MARKERSTYLES[item.props.markerstyle],
        )[0]
        for prop in ["selected", "linewidth", "markersize"]:
            self.set_property(prop, item.get_property(prop))
            self.connect(f"notify::{prop}", self._set_properties)
        self._set_properties(None, None)


class TextItemArtistWrapper(ArtistWrapperBase):
    __gtype_name__ = "TextItemArtistWrapper"

    @GObject.Property(type=float, default=12)
    def size(self) -> float:
        return self._artist.get_fontsize()

    @size.setter
    def size(self, size: float):
        self._artist.set_fontsize(size)

    @GObject.Property(type=int, default=0, minimum=0, maximum=360)
    def rotation(self) -> int:
        return self._artist.get_rotation()

    @rotation.setter
    def rotation(self, rotation: int):
        self._artist.set_rotation(rotation)

    @GObject.Property(type=str, default="")
    def text(self) -> str:
        return self._artist.get_text()

    @text.setter
    def text(self, text: str):
        self._artist.set_text(text)

    @GObject.Property(type=float, default=0)
    def xanchor(self) -> float:
        return self._artist.get_position()[0]

    @xanchor.setter
    def xanchor(self, xanchor: float):
        self._artist.set_position((xanchor, self.props.yanchor))

    @GObject.Property(type=float, default=0)
    def yanchor(self) -> float:
        return self._artist.get_position()[1]

    @yanchor.setter
    def yanchor(self, yanchor: float):
        self._artist.set_position((self.props.xanchor, yanchor))

    def __init__(self, axis, item):
        super().__init__()
        self._artist = axis.text(
            item.props.xanchor, item.props.yanchor, item.props.text,
            label=utilities.shorten_label(item.props.name, 40), clip_on=True,
            color=item.props.color, alpha=item.props.alpha,
            fontsize=item.props.size, rotation=item.props.rotation,
        )
