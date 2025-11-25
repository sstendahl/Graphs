# SPDX-License-Identifier: GPL-3.0-or-later
"""
Wrapper classes for mpl artists.

Provides GObject based wrappers for mpl artists.
"""
from gi.repository import GObject, Graphs

from graphs import misc, scales, utilities

from matplotlib import artist, pyplot
from matplotlib.figure import Figure

import numpy

import sympy
from sympy.calculus.singularities import singularities


def _ellipsize(name: str) -> str:
    return name[:40] + "…" if len(name) > 40 else name


def new_for_item(fig: Figure, item: Graphs.Item):
    """
    Create a new artist for an item.

    Creates bindings between item and artist properties so changes are handled
    automatically.
    """
    match item.__gtype_name__:
        case "GraphsDataItem":
            cls = DataItemArtistWrapper
        case "GraphsGeneratedDataItem":
            cls = GeneratedDataItemArtistWrapper
        case "GraphsEquationItem":
            cls = EquationItemArtistWrapper
        case "GraphsFillItem":
            cls = FillItemArtistWrapper
        case "GraphsTextItem":
            cls = TextItemArtistWrapper
        case _:
            pass
    artist_wrapper = cls(
        fig.axes[item.get_yposition() * 2 + item.get_xposition()],
        item,
    )
    for prop in dir(artist_wrapper.props):
        if not (prop == "label" and artist_wrapper.legend):
            item.bind_property(prop, artist_wrapper, prop, 0)
    artist_wrapper.connect("notify", lambda _x, _y: fig.update_legend())
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
        self._artist.set_label(_ellipsize(name))

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
    def data(self) -> tuple[list, list]:
        """Get data property."""
        return self._artist.get_data()

    @data.setter
    def data(self, data: tuple[list, list]) -> None:
        """Set data property."""
        self._artist.set_data(data)

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
            item.get_xdata(),
            item.get_ydata(),
            label=_ellipsize(item.get_name()),
            color=item.get_color(),
            alpha=item.get_alpha(),
            linestyle=misc.LINESTYLES[item.props.linestyle],
            marker=misc.MARKERSTYLES[item.props.markerstyle],
        )[0]
        for prop in ("selected", "linewidth", "markersize"):
            self.set_property(prop, item.get_property(prop))
            self.connect(f"notify::{prop}", self._set_properties)
        self._set_properties(None, None)


class SingularityHandler:
    """Mix-in class for handling singularities in equation-based plots."""

    def _find_singularities(self, limits: tuple[float, float]) -> set:
        """Find singularities within the given limits."""
        x = sympy.Symbol("x")
        expr = sympy.sympify(self._equation)
        domain = sympy.Interval(*limits)
        return singularities(expr, x, domain)

    def _insert_singularity_points(
            self,
            xdata: list,
            ydata: list,
            singularities: set,
            ylim: tuple[float, float],
            insert_y_points: bool = True) -> tuple:
        """Insert NaN and optionally infinite value points at singularities."""
        xdata = numpy.array(xdata)
        ydata = numpy.array(ydata)
        # TODO: THIS IS A BIT BUGGED WITH EDGE-CASES WHERE VALUES ARE LARGE,
        # AND FAR AWAY FROM THE CURRENT CANVAS LIMITS
        inf_value = abs(ylim[1] - ylim[0]) * 2

        if insert_y_points:
            x_min, x_max = float(xdata.min()), float(xdata.max())
            x_range = abs(x_max - x_min)
            epsilon = x_range * 0.001

        for singularity in sorted(singularities, reverse=True):
            x_value = float(singularity)
            insert_idx = numpy.searchsorted(xdata, x_value)

            if insert_y_points:
                left_sign = numpy.sign(ydata[insert_idx - 1])
                right_sign = numpy.sign(ydata[insert_idx])
                xdata = numpy.insert(xdata, insert_idx,
                                     [x_value - epsilon,
                                      x_value,
                                      x_value + epsilon])
                ydata = numpy.insert(ydata, insert_idx,
                                     [left_sign * inf_value,
                                      numpy.nan,
                                      right_sign * inf_value])
            else:
                xdata = numpy.insert(xdata, insert_idx, x_value)
                ydata = numpy.insert(ydata, insert_idx, numpy.nan)
        return xdata, ydata


class GeneratedDataItemArtistWrapper(SingularityHandler,
                                     DataItemArtistWrapper):
    """Wrapper for GeneratedDataItemArtist."""

    __gtype_name__ = "GraphsGeneratedDataItemArtistWrapper"

    def handle_singularities(self, data: tuple[list, list]) -> None:
        """Handle singularities and update artist data."""
        xdata, ydata = numpy.asarray(data[0]), numpy.asarray(data[1])
        x_min, x_max = float(numpy.min(xdata)), float(numpy.max(xdata))

        singularities = self._find_singularities((x_min, x_max))
        if singularities:
            ylim = self._axis.get_ylim()
            xdata, ydata = self._insert_singularity_points(
                xdata, ydata, singularities, ylim, insert_y_points=False,
            )

        self._artist.set_data(xdata, ydata)

    @GObject.Property(type=str, flags=2)
    def equation(self) -> None:
        """Write-only property, ignored."""

    @equation.setter
    def equation(self, equation: str) -> None:
        self._equation = utilities.preprocess(equation)
        self.handle_singularities(self._artist.get_data())

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        self._axis = axis
        super().__init__(self._axis, item)
        self._equation = utilities.preprocess(item.props.equation)


class EquationItemArtistWrapper(SingularityHandler, ItemArtistWrapper):
    """Wrapper for EquationItem."""

    __gtype_name__ = "GraphsEquationItemArtistWrapper"
    selected = GObject.Property(type=bool, default=True)
    linewidth = GObject.Property(type=float, default=3)
    legend = True

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        super().__init__()

        self._equation = utilities.preprocess(item.props.equation)
        self._axis = axis
        axis.callbacks.connect("xlim_changed", self._on_xlim)
        self._artist = axis.plot(
            [],
            [],
            label=_ellipsize(item.get_name()),
            color=item.get_color(),
            alpha=item.get_alpha(),
            linestyle=misc.LINESTYLES[item.props.linestyle + 1],
            marker="none",
        )[0]
        for prop in ("selected", "linewidth"):
            self.set_property(prop, item.get_property(prop))
            self.connect(f"notify::{prop}", self._set_properties)
        self._set_properties(None, None)
        self._generate_data()

    @GObject.Property(type=str, flags=2)
    def equation(self) -> None:
        """Write-only property, ignored."""

    def handle_singularities(self, data: tuple[list, list]) -> None:
        """Handle singularities and update artist data."""
        xdata, ydata = numpy.asarray(data[0]), numpy.asarray(data[1])
        x_min, x_max = float(numpy.min(xdata)), float(numpy.max(xdata))

        singularities = self._find_singularities((x_min, x_max))
        if singularities:
            ylim = self._axis.get_ylim()
            xdata, ydata = self._insert_singularity_points(
                xdata, ydata, singularities, ylim, insert_y_points=True,
            )

        self._artist.set_data(xdata, ydata)

    @equation.setter
    def equation(self, equation: str) -> None:
        self._equation = utilities.preprocess(equation)
        self._generate_data()
        self.handle_singularities(self._artist.get_data())

    @GObject.Property(type=int, default=1)
    def linestyle(self) -> int:
        """Get linestyle property."""
        return misc.LINESTYLES.index(self._artist.get_linestyle()) - 1

    @linestyle.setter
    def linestyle(self, linestyle: int) -> None:
        """Set linestyle property."""
        self._artist.set_linestyle(misc.LINESTYLES[linestyle + 1])

    def _set_properties(self, _x, _y) -> None:
        linewidth = self.props.linewidth
        if not self.props.selected:
            linewidth *= 0.35
        self._artist.set_linewidth(linewidth)

    def _on_xlim(self, _axis):
        self._generate_data()

    def _generate_data(self):
        """Generate new data for the artist."""
        x_start, x_stop = self._axis.get_xlim()
        scale = scales.Scale.from_string(self._axis.get_xscale())

        limits = (
            utilities.get_value_at_fraction(-1, x_start, x_stop, scale),
            utilities.get_value_at_fraction(2, x_start, x_stop, scale),
        )

        xdata, ydata = utilities.equation_to_data(
            self._equation, limits, scale=scale,
        )

        singularities = self._find_singularities(limits)
        if singularities:
            #TODO: FIX Y-INSERTION
            ylim = self._axis.get_ylim()
            xdata, ydata = self._insert_singularity_points(
                xdata, ydata, singularities, ylim, insert_y_points=False,
            )

        self._artist.set_data(xdata, ydata)
        self._axis.figure.canvas.queue_draw()


class TextItemArtistWrapper(ItemArtistWrapper):
    """Wrapper for TextItem."""

    __gtype_name__ = "GraphsTextItemArtistWrapper"

    @GObject.Property(type=float, default=12)
    def size(self) -> float:
        """Get size property."""
        return self._artist.get_fontsize()

    @size.setter
    def size(self, size: float) -> None:
        """Set size property."""
        self._artist.set_fontsize(size)

    @GObject.Property(type=int, default=0, minimum=0, maximum=360)
    def rotation(self) -> int:
        """Get rotation property."""
        return self._artist.get_rotation()

    @rotation.setter
    def rotation(self, rotation: int) -> None:
        """Set rotation property."""
        self._artist.set_rotation(rotation)

    @GObject.Property(type=str, default="")
    def text(self) -> str:
        """Get text property."""
        return self._artist.get_text()

    @text.setter
    def text(self, text: str) -> None:
        """Set text property."""
        self._artist.set_text(text)

    @GObject.Property(type=float, default=0)
    def xanchor(self) -> float:
        """Get xanchor property."""
        return self._artist.get_position()[0]

    @xanchor.setter
    def xanchor(self, xanchor: float) -> None:
        """Set xanchor property."""
        self._artist.set_position((xanchor, self.props.yanchor))

    @GObject.Property(type=float, default=0)
    def yanchor(self) -> float:
        """Get yanchor property."""
        return self._artist.get_position()[1]

    @yanchor.setter
    def yanchor(self, yanchor: float) -> None:
        """Set yanchor property."""
        self._artist.set_position((self.props.xanchor, yanchor))

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        super().__init__()
        self._artist = axis.text(
            item.props.xanchor,
            item.props.yanchor,
            item.props.text,
            label=_ellipsize(item.get_name()),
            color=item.get_color(),
            alpha=item.get_alpha(),
            clip_on=True,
            fontsize=item.props.size,
            rotation=item.props.rotation,
        )


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
            label=_ellipsize(item.get_name()),
            color=item.get_color(),
            alpha=item.get_alpha(),
        )
