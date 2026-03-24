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
from sympy.calculus.singularities import singularities as find_singularities


def _ellipsize(name: str) -> str:
    return name[:40] + "…" if len(name) > 40 else name


def new_for_item(fig: Figure, item: Graphs.Item):
    """
    Create a new artist for an item.

    Creates bindings between item and artist properties so changes are handled
    automatically.
    """
    match item.__gtype_name__:
        case "GraphsPythonDataItem":
            cls = DataItemArtistWrapper
        case "GraphsPythonGeneratedDataItem":
            cls = DataItemArtistWrapper
        case "GraphsPythonEquationItem":
            cls = EquationItemArtistWrapper
        case "GraphsPythonFillItem":
            cls = FillItemArtistWrapper
        case "GraphsPythonTextItem":
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
    def data(self) -> tuple[list, list, list, list]:
        """Get data property."""
        raise NotImplementedError

    @data.setter
    def data(self, data: tuple[list, list, list, list]) -> None:
        """Set data property."""
        xdata, ydata, xerr, yerr = self._handle_singularities(data)
        self._data.set_data((xdata, ydata))

        if xerr is not None:
            start = numpy.column_stack((xdata - xerr, ydata))
            end = numpy.column_stack((xdata + xerr, ydata))
            self._xbar.set_segments(numpy.stack((start, end), axis=1))
            self._xcaps[0].set_data(xdata - xerr, ydata)
            self._xcaps[1].set_data(xdata + xerr, ydata)

        if yerr is not None:
            start = numpy.column_stack((xdata, ydata - yerr))
            end = numpy.column_stack((xdata, ydata + yerr))
            self._ybar.set_segments(numpy.stack((start, end), axis=1))
            self._ycaps[0].set_data(xdata, ydata - yerr)
            self._ycaps[1].set_data(xdata, ydata + yerr)

    @GObject.Property(type=bool, default=True)
    def showxerr(self) -> bool:
        """Get showxerr property."""
        raise NotImplementedError

    @showxerr.setter
    def showxerr(self, showxerr: bool) -> None:
        """Set showxerr property."""
        self._xbar.set_visible(showxerr)
        for cap in self._xcaps:
            cap.set_visible(showxerr)

    @GObject.Property(type=bool, default=True)
    def showyerr(self) -> bool:
        """Get showyerr property."""
        raise NotImplementedError

    @showyerr.setter
    def showyerr(self, showyerr: bool) -> None:
        """Set showyerr property."""
        self._ybar.set_visible(showyerr)
        for cap in self._ycaps:
            cap.set_visible(showyerr)

    @GObject.Property(type=int, default=1)
    def linestyle(self) -> int:
        """Get linestyle property."""
        return misc.LINESTYLES.index(self._data.get_linestyle())

    @linestyle.setter
    def linestyle(self, linestyle: int) -> None:
        """Set linestyle property."""
        self._data.set_linestyle(misc.LINESTYLES[linestyle])

    @GObject.Property(type=int, default=1)
    def markerstyle(self) -> int:
        """Get markerstyle property."""
        return misc.MARKERSTYLES.index(self._data.get_marker())

    @markerstyle.setter
    def markerstyle(self, markerstyle: int) -> None:
        """Set markerstyle property."""
        self._data.set_marker(misc.MARKERSTYLES[markerstyle])

    @GObject.Property(type=float, default=0)
    def errcapsize(self) -> float:
        """Get errcapsize property."""
        raise NotImplementedError

    @errcapsize.setter
    def errcapsize(self, errcapsize: float) -> None:
        """Set errcapsize property."""
        for cap in self._caps:
            cap.set_markersize(errcapsize * 2)

    @GObject.Property(type=float, default=1)
    def errcapthick(self) -> float:
        """Get errcapthick property."""
        raise NotImplementedError

    @errcapthick.setter
    def errcapthick(self, errcapthick: float) -> None:
        """Set errcapthick property."""
        for cap in self._caps:
            cap.set_markeredgewidth(errcapthick)

    @GObject.Property(type=float, default=1)
    def errlinewidth(self) -> float:
        """Get errlinewidth property."""
        raise NotImplementedError

    @errlinewidth.setter
    def errlinewidth(self, errlinewidth: float) -> None:
        """Set errlinewidth property."""
        for bar in self._bars:
            bar.set_linewidth(errlinewidth)

    @GObject.Property(type=bool, default=False)
    def errbarsabove(self) -> bool:
        """Get errbarsabove property."""
        raise NotImplementedError

    @errbarsabove.setter
    def errbarsabove(self, errbarsabove: bool) -> None:
        """Set errbarsabove property."""
        zorder = self._data.get_zorder()
        offset = 1 if errbarsabove else -1
        for bar in self._bars:
            bar.set_zorder(zorder + offset)

    @GObject.Property(type=str, default="")
    def errcolor(self) -> str:
        """Get errcolor property."""
        raise NotImplementedError

    @errcolor.setter
    def errcolor(self, errcolor: str) -> None:
        """Set errcolor property."""
        if not errcolor:
            return

        for bar in self._bars:
            bar.set_color(errcolor)
        for cap in self._caps:
            cap.set_color(errcolor)
            cap.set_markerfacecolor(errcolor)
            cap.set_markeredgecolor(errcolor)

    def _set_properties(self, *_args) -> None:
        linewidth, markersize = self.props.linewidth, self.props.markersize
        if not self.props.selected:
            linewidth *= 0.35
            markersize *= 0.35
        self._data.set_linewidth(linewidth)
        self._data.set_markersize(markersize)

    @staticmethod
    def _handle_singularities(data: tuple) -> tuple:
        """Adjust data to handle singularity jumps."""
        xdata, ydata = map(numpy.asarray, data[:2])
        xerr = None if data[2] is None else numpy.asarray(data[2])
        yerr = None if data[3] is None else numpy.asarray(data[3])

        mask = numpy.abs(numpy.gradient(ydata, xdata))[:-1] > 20
        mask &= numpy.sign(ydata[:-1]) != numpy.sign(ydata[1:])

        edges = numpy.diff(mask.astype(int))
        starts = numpy.where(edges == 1)[0] + 1
        ends = numpy.where(edges == -1)[0] + 1

        if mask[0]:
            starts = numpy.r_[0, starts]
        if mask[-1]:
            ends = numpy.r_[ends, len(mask)]

        mask = numpy.zeros_like(mask, dtype=bool)
        mask[(starts + ends) // 2] = True

        bad_points = numpy.zeros(len(xdata), dtype=bool)
        left = numpy.abs(ydata[:-1]) > numpy.abs(ydata[1:])
        bad_points[:-1] |= mask & left
        bad_points[1:] |= mask & ~left

        xdata[bad_points] = numpy.nan
        ydata[bad_points] = numpy.nan

        if xerr is not None:
            xerr[bad_points] = numpy.nan

        if yerr is not None:
            yerr[bad_points] = numpy.nan

        return xdata, ydata, xerr, yerr

    def __init__(self, axis: pyplot.axis, item: Graphs.Item) -> None:
        super().__init__()
        xdata, ydata, xerr, yerr = self._handle_singularities(item.props.data)
        self._artist = axis.errorbar(
            xdata,
            ydata,
            xerr=xerr,
            yerr=yerr,
            label=_ellipsize(item.get_name()),
            color=item.get_color(),
            alpha=item.get_alpha(),
            linestyle=misc.LINESTYLES[item.get_linestyle()],
            marker=misc.MARKERSTYLES[item.get_markerstyle()],
            capsize=item.get_errcapsize(),
            capthick=item.get_errcapthick(),
            elinewidth=item.get_errlinewidth(),
            barsabove=item.get_errbarsabove(),
            ecolor=item.get_errcolor(),
        )

        self._data, self._caps, self._bars = self._artist

        # We iterate over bar and caps in assignments to handle all
        # combinations with error bars on either or both axes.
        bar_iter = iter(self._bars)
        cap_iter = iter(self._caps)
        if xerr is not None:
            self._xbar = next(bar_iter)
            self._xcaps = (next(cap_iter), next(cap_iter))
            if not item.get_showxerr():
                self._xbar.set_visible(False)
                for cap in self._xcaps:
                    cap.set_visible(False)
        if yerr is not None:
            self._ybar = next(bar_iter)
            self._ycaps = (next(cap_iter), next(cap_iter))
            if not item.get_showyerr():
                self._ybar.set_visible(False)
                for cap in self._ycaps:
                    cap.set_visible(False)

        for prop in ("selected", "linewidth", "markersize"):
            self.set_property(prop, item.get_property(prop))
            self.connect(f"notify::{prop}", self._set_properties)
        self._set_properties()


class EquationItemArtistWrapper(ItemArtistWrapper):
    """Wrapper for EquationItem."""

    __gtype_name__ = "GraphsEquationItemArtistWrapper"
    selected = GObject.Property(type=bool, default=True)
    linewidth = GObject.Property(type=float, default=3)
    legend = True
    _singularities_cache = {}
    _x = sympy.Symbol("x")

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        super().__init__()

        equation = item.get_preprocessed_equation()
        self._equation = equation
        self._expr = sympy.sympify(equation)
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
        self._expr = sympy.sympify(equation)
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

        lower = utilities.get_value_at_fraction(-1, x_start, x_stop, scale)
        upper = utilities.get_value_at_fraction(2, x_start, x_stop, scale)
        limits = (lower, upper)

        data = utilities.equation_to_data(self._equation, limits, scale=scale)
        singularities = self._find_singularities(limits)
        data = self._insert_singularity_points(data, singularities)

        self._artist.set_data(*data)
        self._axis.figure.parent.queue_draw()

    def _find_singularities(self, limits):
        lower, upper = limits

        cached = self._singularities_cache.get(self._equation)
        if cached:
            cached_min, cached_max = cached["limits"]

            if lower >= cached_min and upper <= cached_max:
                return {
                    s
                    for s in cached["singularities"] if lower <= s <= upper
                }

            x_min, x_max = min(lower, cached_min), max(upper, cached_max)
        else:
            x_min, x_max = lower, upper

        domain = sympy.Interval(x_min, x_max)
        all_singularities = find_singularities(self._expr, self._x, domain)

        self._singularities_cache[self._equation] = {
            "limits": (x_min, x_max),
            "singularities": all_singularities,
        }

        return {s for s in all_singularities if lower <= s <= upper}

    def _insert_singularity_points(self, data, singularities) -> tuple:
        """Insert NaN and infinite value points at singularities."""
        if not singularities:
            return data

        xdata, ydata = map(numpy.asarray, data)

        singularities_arr = numpy.fromiter(sorted(singularities), dtype=float)
        sing_indices = numpy.searchsorted(xdata, singularities_arr)

        ylim = self._axis.get_ylim()
        ylim_range = abs(ylim[1] - ylim[0])
        ydata_range = numpy.nanmax(ydata) - numpy.nanmin(ydata)

        inf_value = max(ylim_range * 1.5, ydata_range * 1.5) * 2
        epsilon = abs(xdata[1] - xdata[0]) / 100

        x_parts, y_parts = [], []

        prev_idx = 0
        n = len(ydata)
        for value, idx in zip(singularities_arr, sing_indices):
            x_parts.append(xdata[prev_idx:idx])
            y_parts.append(ydata[prev_idx:idx])

            if 1 < idx < n - 1:
                left = numpy.sign(ydata[idx - 1] - ydata[idx - 2])
                right = -numpy.sign(ydata[idx + 1] - ydata[idx])
                inf = inf_value + ydata[idx]

                x_parts.append([value - epsilon, value, value + epsilon])
                y_parts.append([left * inf, numpy.nan, right * inf])
            else:
                x_parts.append([value])
                y_parts.append([numpy.nan])

            prev_idx = idx

        x_parts.append(xdata[prev_idx:])
        y_parts.append(ydata[prev_idx:])
        return numpy.concatenate(x_parts), numpy.concatenate(y_parts)


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
