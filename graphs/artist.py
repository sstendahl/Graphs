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
    errcapsize = GObject.Property(type=float, default=0)
    errcapthick = GObject.Property(type=float, default=1)
    errlinewidth = GObject.Property(type=float, default=1)
    errbarsabove = GObject.Property(type=bool, default=False)
    errcolor = GObject.Property(type=str, default="")
    legend = True

    def get_artist(self) -> artist:
        """Get underlying mpl artist."""
        return self._errorbar_container

    @GObject.Property(type=str, default="")
    def name(self) -> str:
        """Get name/label property."""
        return self._artist.get_label()

    @name.setter
    def name(self, name: str) -> None:
        """Set name/label property."""
        label = _ellipsize(name)
        self._artist.set_label(label)
        self._errorbar_container.set_label(label)

    @GObject.Property
    def data(self) -> tuple[list, list]:
        """Get data property."""
        return self._artist.get_data()

    @data.setter
    def data(self, data: tuple[list, list]) -> None:
        """Set data property."""
        self._artist.set_data(data)
        self._refresh_errorbars()

    @GObject.Property(type=object)
    def err(self) -> tuple:
        """Get err property."""
        return self._err

    @err.setter
    def err(self, err: tuple[list, list]) -> None:
        """Set err property."""
        self._err = err
        self._refresh_errorbars()

    @GObject.Property(type=bool, default=True)
    def showxerr(self) -> bool:
        """Get showxerr property."""
        return self._show_xerr

    @showxerr.setter
    def showxerr(self, showxerr: bool) -> None:
        """Set showxerr property."""
        self._show_xerr = showxerr
        self._refresh_errorbars()

    @GObject.Property(type=bool, default=True)
    def showyerr(self) -> bool:
        """Get showyerr property."""
        return self._show_yerr

    @showyerr.setter
    def showyerr(self, showyerr: bool) -> None:
        """Set showyerr property."""
        self._show_yerr = showyerr
        self._refresh_errorbars()

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

    def _set_size_properties(self, *_args) -> None:
        linewidth = self.props.linewidth
        markersize = self.props.markersize
        if not self.props.selected:
            linewidth *= 0.35
            markersize *= 0.35
        self._artist.set_linewidth(linewidth)
        self._artist.set_markersize(markersize)

    def _set_errbar_properties(self, *_args) -> None:
        for bar in (self._xbar, self._ybar):
            if bar:
                bar.set_linewidth(self.props.errlinewidth)
                bar.set_color(self.props.errcolor)
        for cap in (*self._xcaps, *self._ycaps):
            cap.set_markersize(self.props.errcapsize * 2)
            cap.set_markeredgewidth(self.props.errcapthick)
            cap.set_color(self.props.errcolor)
            cap.set_markerfacecolor(self.props.errcolor)
            cap.set_markeredgecolor(self.props.errcolor)
        zorder = self._artist.get_zorder()
        offset = 1 if self.props.errbarsabove else -1
        for bar in (self._xbar, self._ybar):
            if bar:
                bar.set_zorder(zorder + offset)

    def _refresh_errorbars(self) -> None:
        """Sync error bar visibility and positions."""
        x_data, y_data = self._artist.get_data()
        x_data = numpy.asarray(x_data)
        y_data = numpy.asarray(y_data)
        x_err, y_err = self._err
        x_err = x_err if self._show_xerr else None
        y_err = y_err if self._show_yerr else None

        # data and err are set as separate property assignments during cut
        # and undo/redo. So only refresh if lengths are in sync:
        if x_err is not None and len(x_err) != len(x_data):
            return
        if y_err is not None and len(y_err) != len(y_data):
            return
        self._apply_updates(x_data, y_data, x_err, y_err)

    def _apply_updates(
        self,
        x_data: numpy.ndarray,
        y_data: numpy.ndarray,
        x_err: numpy.ndarray,
        y_err: numpy.ndarray,
    ) -> None:
        """Update the segments and positions of mpl artists."""
        has_xerr = x_err is not None
        has_yerr = y_err is not None

        if self._xbar:
            self._xbar.set_visible(has_xerr)
            if has_xerr:
                start = numpy.column_stack((x_data - x_err, y_data))
                end = numpy.column_stack((x_data + x_err, y_data))
                self._xbar.set_segments(numpy.stack((start, end), axis=1))

        if self._xcaps:
            for cap in self._xcaps:
                cap.set_visible(has_xerr)
            if has_xerr:
                self._xcaps[0].set_data(x_data - x_err, y_data)
                self._xcaps[1].set_data(x_data + x_err, y_data)

        if self._ybar:
            self._ybar.set_visible(has_yerr)
            if has_yerr:
                start = numpy.column_stack((x_data, y_data - y_err))
                end = numpy.column_stack((x_data, y_data + y_err))
                self._ybar.set_segments(numpy.stack((start, end), axis=1))

        if self._ycaps:
            for cap in self._ycaps:
                cap.set_visible(has_yerr)
            if has_yerr:
                self._ycaps[0].set_data(x_data, y_data - y_err)
                self._ycaps[1].set_data(x_data, y_data + y_err)

    def __init__(self, axis: pyplot.axis, item: Graphs.Item) -> None:
        super().__init__()
        self._err = item.props.err
        self._show_xerr = item.props.showxerr
        self._show_yerr = item.props.showyerr
        x_err, y_err = self._err
        self._errorbar_container = axis.errorbar(
            item.get_xdata(), item.get_ydata(),
            xerr=x_err, yerr=y_err,
            color=item.get_color(), alpha=item.get_alpha(),
            linestyle=misc.LINESTYLES[item.props.linestyle],
            marker=misc.MARKERSTYLES[item.props.markerstyle],
            capsize=item.props.errcapsize,
            capthick=item.props.errcapthick,
            elinewidth=item.props.errlinewidth,
            barsabove=item.props.errbarsabove,
            ecolor=item.get_errcolor(),
        )

        self._artist, caps, barlines = self._errorbar_container

        # We iterate over bar and caps in assignments to handle all
        # combinations with error bars on either or both axes.
        has_xerr, has_yerr = x_err is not None, y_err is not None
        bar_iter = iter(barlines)
        self._xbar = next(bar_iter) if has_xerr else None
        self._ybar = next(bar_iter) if has_yerr else None

        cap_iter = iter(caps)
        self._xcaps = (next(cap_iter), next(cap_iter)) \
            if has_xerr and caps else ()
        self._ycaps = (next(cap_iter), next(cap_iter)) \
            if has_yerr and caps else ()

        self.name = item.get_name()
        for prop in ("selected", "linewidth", "markersize"):
            self.set_property(prop, item.get_property(prop))
            self.connect(f"notify::{prop}", self._set_size_properties)
        self._set_size_properties()

        for prop in ("errcapsize", "errcapthick", "errlinewidth",
                     "errbarsabove", "errcolor"):
            self.set_property(prop, item.get_property(prop))
            self.connect(f"notify::{prop}", self._set_errbar_properties)
        self._set_errbar_properties()


class SingularityHandler:
    """Mix-in class for handling singularities in equation-based plots."""

    _singularities_cache = {}

    def _handle_singularities(
        self,
        data: tuple[list, list],
        insert_y_points: bool,
    ) -> None:
        """Handle singularities and update artist data."""
        xdata, ydata = numpy.asarray(data[0]), numpy.asarray(data[1])
        x_min, x_max = float(numpy.min(xdata)), float(numpy.max(xdata))

        singularities = self._find_singularities((x_min, x_max))
        if singularities:
            xdata, ydata = self._insert_singularity_points(
                xdata, ydata, singularities, self._axis.get_ylim(),
                insert_y_points,
            )

        self._artist.set_data(xdata, ydata)

    def _find_singularities(self, limits: tuple[float, float]) -> set:
        """Find singularities within the given limits."""
        x_min, x_max = limits

        if self._equation in self._singularities_cache:
            cached = self._singularities_cache[self._equation]
            cached_min, cached_max = cached["limits"]

            if x_min >= cached_min and x_max <= cached_max:
                return {
                    s
                    for s in cached["singularities"] if x_min <= s <= x_max
                }

            x_min, x_max = min(x_min, cached_min), max(x_max, cached_max)

        x = sympy.Symbol("x")
        expr = sympy.sympify(self._equation)
        domain = sympy.Interval(x_min, x_max)
        all_singularities = singularities(expr, x, domain)

        self._singularities_cache[self._equation] = {
            "limits": (x_min, x_max),
            "singularities": all_singularities,
        }

        return {s for s in all_singularities if limits[0] <= s <= limits[1]}

    def _insert_singularity_points(
        self,
        xdata,
        ydata,
        singularities,
        ylim,
        insert_y_points=True,
    ) -> tuple:
        """Insert NaN and optionally infinite value points at singularities."""
        if not singularities:
            return xdata, ydata

        xdata = numpy.asarray(xdata, dtype=float)
        ydata = numpy.asarray(ydata, dtype=float)
        singularities_arr = numpy.array(sorted(singularities), dtype=float)
        sing_indices = numpy.searchsorted(xdata, singularities_arr)

        ylim_range = abs(ylim[1] - ylim[0])
        ylim_m = ylim_range / 2
        ydata_range = numpy.nanmax(ydata) - numpy.nanmin(ydata)
        yrange_m = ydata_range / 2
        inf_value = max(ylim_range + ylim_m, ydata_range + yrange_m) * 2
        epsilon = abs(xdata[1] - xdata[0]) / 100

        x_parts, y_parts = [], []
        prev_idx = 0
        for value, insert_idx in zip(singularities_arr, sing_indices):
            x_parts.append(xdata[prev_idx:insert_idx])
            y_parts.append(ydata[prev_idx:insert_idx])

            if insert_y_points and 1 < insert_idx < len(ydata) - 1:
                x_parts.append(self._make_singularity_x(value, epsilon))
                y_parts.append(
                    self._make_singularity_y(ydata, insert_idx, inf_value),
                )
            else:
                x_parts.append(numpy.array([value]))
                y_parts.append(numpy.array([numpy.nan]))

            prev_idx = insert_idx

        x_parts.append(xdata[prev_idx:])
        y_parts.append(ydata[prev_idx:])
        return numpy.concatenate(x_parts), numpy.concatenate(y_parts)

    def _make_singularity_x(self, value, epsilon):
        """Create x-coordinates around singularity."""
        return numpy.array([value - epsilon, value, value + epsilon])

    def _make_singularity_y(self, ydata, insert_idx, inf_value):
        """Create y-coordinates around singularity."""
        left = numpy.sign(ydata[insert_idx - 1] - ydata[insert_idx - 2])
        right = -numpy.sign(ydata[insert_idx + 1] - ydata[insert_idx])
        inf_value += ydata[insert_idx]
        return numpy.array([left * inf_value, numpy.nan, right * inf_value])


class GeneratedDataItemArtistWrapper(
    DataItemArtistWrapper,
    SingularityHandler,
):
    """Wrapper for GeneratedDataItemArtist."""

    __gtype_name__ = "GraphsGeneratedDataItemArtistWrapper"

    @GObject.Property(type=str, flags=2)
    def equation(self) -> None:
        """Write-only property, ignored."""

    @equation.setter
    def equation(self, equation: str) -> None:
        self._singularities_cache.clear()
        self._equation = Graphs.preprocess_equation(equation)
        self._handle_singularities(self._artist.get_data(), False)

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        self._axis = axis
        super().__init__(self._axis, item)
        self._equation = Graphs.preprocess_equation(item.props.equation)


class EquationItemArtistWrapper(ItemArtistWrapper, SingularityHandler):
    """Wrapper for EquationItem."""

    __gtype_name__ = "GraphsEquationItemArtistWrapper"
    selected = GObject.Property(type=bool, default=True)
    linewidth = GObject.Property(type=float, default=3)
    legend = True

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        super().__init__()

        self._equation = Graphs.preprocess_equation(item.props.equation)
        self._axis = axis
        self._view_change_timeout_id = None
        if self._axis.figure.parent is not None:
            self._axis.figure.parent.connect(
                "view_changed",
                self._on_view_change,
            )
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

    def _on_view_change(self, *_args):
        """Debounced view change handler that generates data after delay."""
        if self._view_change_timeout_id is not None:
            GObject.source_remove(self._view_change_timeout_id)

        def _timeout_callback():
            self._view_change_timeout_id = None
            self._generate_data()
            return False

        self._view_change_timeout_id = \
            GObject.timeout_add(100, _timeout_callback)

    @GObject.Property(type=str, flags=2)
    def equation(self) -> None:
        """Write-only property, ignored."""

    @equation.setter
    def equation(self, equation: str) -> None:
        self._singularities_cache.clear()
        self._equation = Graphs.preprocess_equation(equation)
        self._generate_data()

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

        self._artist.set_data(xdata, ydata)
        self._handle_singularities(self._artist.get_data(), True)
        self._axis.figure.parent.queue_draw()


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
