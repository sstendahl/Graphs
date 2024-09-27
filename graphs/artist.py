# SPDX-License-Identifier: GPL-3.0-or-later
"""
Wrapper classes for mpl artists.

Provides GObject based wrappers for mpl artists.
"""
import contextlib

from gi.repository import GObject, Graphs

from graphs import misc, utilities

from matplotlib import artist, pyplot
from matplotlib.figure import Figure


def new_for_item(canvas: Graphs.Canvas, item: Graphs.Item):
    """
    Create a new artist for an item.

    Creates bindings between item and artist properties so changes are handled
    automatically.
    """
    match item.__gtype_name__:
        case "GraphsDataItem":
            cls = DataItemArtistWrapper
        case "GraphsEquationItem":
            cls = EquationItemArtistWrapper
        case "GraphsFillItem":
            cls = FillItemArtistWrapper
        case "GraphsTextItem":
            cls = TextItemArtistWrapper
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
    """Wrapper for base Item."""

    __gtype_name__ = "GraphsItemArtistWrapper"
    legend = False

    def get_artist(self) -> artist:
        """Get underlying mpl artist."""
        return self._artist

    @GObject.Property(type=str, default="")
    def name(self) -> str:
        """Get name/label property."""
        return self._artist.get_label()

    @name.setter
    def name(self, name: str) -> None:
        """Set name/label property."""
        self._artist.set_label(Graphs.tools_shorten_label(name, 40))

    @GObject.Property(type=str, default="000000")
    def color(self) -> str:
        """Get color property."""
        return self._artist.get_color()

    @color.setter
    def color(self, color: str) -> None:
        """Set color property."""
        self._artist.set_color(color)

    @GObject.Property(type=float, default=1)
    def alpha(self) -> float:
        """Get alpha property."""
        return self._artist.get_alpha()

    @alpha.setter
    def alpha(self, alpha: float) -> None:
        """Set alpha property."""
        self._artist.set_alpha(alpha)


class DataItemArtistWrapper(ItemArtistWrapper):
    """Wrapper for DataItem."""

    __gtype_name__ = "GraphsDataItemArtistWrapper"
    selected = GObject.Property(type=bool, default=True)
    linewidth = GObject.Property(type=float, default=3)
    markersize = GObject.Property(type=float, default=7)
    legend = True

    @GObject.Property
    def xdata(self) -> list:
        """Get xdata property."""
        return self._artist.get_xdata()

    @xdata.setter
    def xdata(self, xdata: list) -> None:
        """Set xdata property."""
        self._artist.set_xdata(xdata)

    @GObject.Property
    def ydata(self) -> list:
        """Get ydata property."""
        return self._artist.get_ydata()

    @ydata.setter
    def ydata(self, ydata: list) -> None:
        """Set ydata property."""
        self._artist.set_ydata(ydata)

    @GObject.Property(type=int, default=1)
    def linestyle(self) -> int:
        """Get linestyle property."""
        return misc.LINESTYLES.index(self._artist.get_linestyle())

    @linestyle.setter
    def linestyle(self, linestyle: int) -> None:
        """Set linestyle property."""
        self._artist.set_linestyle(misc.LINESTYLES[linestyle])

    @GObject.Property(type=int, default=1)
    def markerstyle(self) -> int:
        """Get markerstyle property."""
        return misc.MARKERSTYLES.index(self._artist.get_marker())

    @markerstyle.setter
    def markerstyle(self, markerstyle: int) -> None:
        """Set markerstyle property."""
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
            label=Graphs.tools_shorten_label(item.get_name(), 40),
            color=item.get_color(),
            alpha=item.get_alpha(),
            linestyle=misc.LINESTYLES[item.props.linestyle],
            marker=misc.MARKERSTYLES[item.props.markerstyle],
        )[0]
        for prop in ("selected", "linewidth", "markersize"):
            self.set_property(prop, item.get_property(prop))
            self.connect(f"notify::{prop}", self._set_properties)
        self._set_properties(None, None)


class EquationItemArtistWrapper(ItemArtistWrapper):
    """Wrapper for EquationItem."""

    __gtype_name__ = "GraphsEquationItemArtistWrapper"
    selected = GObject.Property(type=bool, default=True)
    linewidth = GObject.Property(type=float, default=3)

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        super().__init__()

        self._equation = utilities.preprocess(item.props.equation)
        self._axis = axis
        self._axis.callbacks.connect("xlim_changed", self._generate_data)
        self._artist = axis.plot(
            [],
            [],
            label=Graphs.tools_shorten_label(item.get_name(), 40),
            color=item.get_color(),
            alpha=item.get_alpha(),
            linestyle=misc.LINESTYLES[item.props.linestyle],
        )[0]
        for prop in ("selected", "linewidth"):
            self.set_property(prop, item.get_property(prop))
            self.connect(f"notify::{prop}", self._set_properties)
        self._set_properties(None, None)
        self._generate_data()

    @GObject.Property(type=str, flags=2)
    def equation(self) -> None:
        """Write-only property, ignored."""

    @equation.setter
    def equation(self, equation: str) -> None:
        self._equation = utilities.preprocess(equation)
        self._generate_data()

    @GObject.Property(type=int, default=1)
    def linestyle(self) -> int:
        """Get linestyle property."""
        return misc.LINESTYLES.index(self._artist.get_linestyle())

    @linestyle.setter
    def linestyle(self, linestyle: int) -> None:
        """Set linestyle property."""
        self._artist.set_linestyle(misc.LINESTYLES[linestyle])

    def _set_properties(self, _x, _y) -> None:
        linewidth = self.props.linewidth
        if not self.props.selected:
            linewidth *= 0.35
        self._artist.set_linewidth(linewidth)

    def _generate_data(self, _axis = None):
        """Generate new data for the artist."""
        x_start, x_stop = self._axis.get_xlim()
        x_range = x_stop - x_start
        limits = (x_start - 0.25 * x_range, x_stop + 0.25 * x_range)
        xdata, ydata = utilities.equation_to_data(self._equation, limits)
        self._artist.set_data(xdata, ydata)
        canvas = self._axis.figure.canvas
        canvas.queue_draw()


class FillItemArtistWrapper(ItemArtistWrapper):
    """Wrapper for FillItem."""

    __gtype_name__ = "GraphsFillItemArtistWrapper"

    @GObject.Property(type=object, flags=2)
    def data(self) -> None:
        """Write-only property, ignored."""

    @data.setter
    def data(self, data) -> None:
        dummy = Figure().add_subplot().fill_between(*data)
        self._artist.set_paths([dummy.get_paths()[0].vertices])

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        super().__init__()
        self._artist = axis.fill_between(
            *item.props.data,
            label=Graphs.tools_shorten_label(item.get_name(), 40),
            color=item.get_color(),
            alpha=item.get_alpha(),
        )
