# SPDX-License-Identifier: GPL-3.0-or-later
"""
Wrapper classes for mpl artists.

Provides GObject based wrappers for mpl artists.
"""
from itertools import islice

from gi.repository import GObject, Graphs

from graphs import ast, misc, utilities

from matplotlib import artist, pyplot
from matplotlib.figure import Figure

import numpy

from scipy.stats import median_abs_deviation

import sympy
from sympy.calculus.singularities import singularities as find_singularities


def _find_row_extrema(rows):
    """Find the position of the min and max within each row, ignoring NaN."""
    blanked = numpy.isnan(rows)
    return (
        numpy.where(blanked, numpy.inf, rows).argmin(axis=1),
        numpy.where(blanked, -numpy.inf, rows).argmax(axis=1),
    )


def _decimate(x_keys, ydata, nan_indices, sorted_x, x_start, x_stop, pixels):
    """Return the indices that will be drawn."""
    point_count = len(ydata)
    if point_count < Graphs.DOWNSAMPLE_THRESHOLD:
        return None

    first, last = 0, point_count
    if sorted_x:
        view_low, view_high = min(x_start, x_stop), max(x_start, x_stop)
        first = max(0, int(numpy.searchsorted(x_keys, view_low, "left")) - 1)
        last = min(
            point_count,
            int(numpy.searchsorted(x_keys, view_high, "right")) + 1,
        )

    bucket_count = max(128, int(pixels))
    visible_count = last - first
    if visible_count <= bucket_count * 2:
        if visible_count == point_count:
            return None
        return numpy.arange(first, last)

    bucket_size = visible_count // bucket_count
    bucketed_end = first + bucket_size * bucket_count
    buckets = ydata[first:bucketed_end].reshape(bucket_count, bucket_size)
    bucket_starts = first + numpy.arange(bucket_count) * bucket_size
    lowest = buckets.argmin(axis=1) + bucket_starts
    highest = buckets.argmax(axis=1) + bucket_starts
    selected = [lowest, highest, numpy.array((first, last - 1))]

    gaps = nan_indices[(nan_indices >= first) & (nan_indices < last)]
    if gaps.size:
        selected += _fix_nan_extrema(
            gaps, buckets, bucket_starts, bucket_size, first, bucketed_end,
            lowest, highest,
        )

    if bucketed_end < last:  # remainder that did not fill a whole bucket
        remainder = ydata[bucketed_end:last].reshape(1, -1)
        selected.append(bucketed_end + numpy.concatenate(
            _find_row_extrema(remainder),
        ))
    return numpy.unique(numpy.concatenate(selected))


def _fix_nan_extrema(gaps, buckets, bucket_starts, bucket_size, first,
                     bucketed_end, lowest, highest):
    """Pick better extrema for the buckets that contain a NaN."""
    bucketed_gaps = gaps[gaps < bucketed_end]
    gap_buckets, first_of_bucket = numpy.unique(
        (bucketed_gaps - first) // bucket_size,
        return_index=True,
    )
    low_within, high_within = _find_row_extrema(buckets[gap_buckets])
    lowest[gap_buckets] = bucket_starts[gap_buckets] + low_within
    highest[gap_buckets] = bucket_starts[gap_buckets] + high_within

    breaks = [bucketed_gaps[first_of_bucket]]
    trailing_gaps = gaps[gaps >= bucketed_end]
    if trailing_gaps.size:
        breaks.append(trailing_gaps[:1])
    return breaks


def new_for_item(fig: Figure, item: Graphs.Item) -> GObject.Object:
    """
    Create a new artist for an item.

    Creates bindings between item and artist properties so changes are handled
    automatically.
    """
    if isinstance(item, Graphs.DataItem):
        cls = DataItemArtistWrapper
    elif isinstance(item, Graphs.EquationItem):
        cls = EquationItemArtistWrapper
    elif isinstance(item, Graphs.TextItem):
        cls = TextItemArtistWrapper
    elif isinstance(item, Graphs.FillItem):
        cls = FillItemArtistWrapper
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
        self._artist.set_label(name)

    @GObject.Property(type=str, default="000000")
    def color(self) -> str:
        """Get color property."""
        return self._color_artist.get_color()

    @color.setter
    def color(self, color: str) -> None:
        """Set color property."""
        self._color_artist.set_color(color)

    @GObject.Property(type=float, default=1)
    def alpha(self) -> float:
        """Get alpha property."""
        return self._color_artist.get_alpha()

    @alpha.setter
    def alpha(self, alpha: float) -> None:
        """Set alpha property."""
        self._artist.set_alpha(alpha)

    @GObject.Property(type=bool, default=True)
    def visible(self) -> bool:
        """Get visible property."""
        return self._artist.get_visible()

    @visible.setter
    def visible(self, visible: bool) -> None:
        """Set visible property."""
        self._artist.set_visible(visible)


class DataItemArtistWrapper(ItemArtistWrapper):
    """Wrapper for DataItem."""

    __gtype_name__ = "GraphsDataItemArtistWrapper"
    selected = GObject.Property(type=bool, default=True)
    linewidth = GObject.Property(type=float, default=3)
    markersize = GObject.Property(type=float, default=7)
    legend = GObject.Property(type=bool, default=True)
    downsample = GObject.Property(type=bool, default=True)

    @GObject.Property(type=Graphs.DataHolder)
    def data(self) -> Graphs.DataHolder:
        """Get data property."""
        raise NotImplementedError

    @data.setter
    def data(self, data: Graphs.DataHolder) -> None:
        """Set data property."""
        self._store(data)
        self._apply_lod()

    def _store(self, data: Graphs.DataHolder) -> None:
        """Cache the full resolution data."""
        self._full = self._handle_singularities(data)
        xdata = self._full[0]
        step = numpy.diff(xdata)
        self._sorted = bool(numpy.all(step[~numpy.isnan(step)] >= 0))
        self._keys = numpy.maximum.accumulate(
            numpy.nan_to_num(xdata, nan=-numpy.inf),
        ) if numpy.isnan(xdata).any() else xdata
        self._nans = numpy.flatnonzero(numpy.isnan(self._full[1]))

    def _queue_lod(self, *_args) -> None:
        """Debounce level of detail updates while panning or resizing."""
        if self._lod_timeout_id is not None:
            GObject.source_remove(self._lod_timeout_id)
        self._lod_timeout_id = GObject.timeout_add(
            100, self._lod_timeout_callback)

    def _lod_timeout_callback(self) -> bool:
        self._lod_timeout_id = None
        self._apply_lod()
        if self._axis.figure.parent is not None:
            self._axis.figure.parent.queue_draw()
        return False

    def _apply_lod(self, *_args) -> None:
        """Draw at a level of detail matching the current view."""
        xdata, ydata, xerr, yerr = self._full
        decimate = self.props.downsample \
            and self._axis.figure.parent is not None
        indices = _decimate(
            self._keys, ydata, self._nans, self._sorted,
            *self._axis.get_xlim(), self._axis.bbox.width,
        ) if decimate else None
        if indices is not None:
            xdata, ydata = xdata[indices], ydata[indices]
            xerr = None if xerr is None else xerr[indices]
            yerr = None if yerr is None else yerr[indices]
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

    def _apply_visibility(self) -> None:
        """Apply the combined visibility flags to line, bars and caps."""
        self._data.set_visible(self._visible)
        for bar, caps, show in (
            (self._xbar, self._xcaps, self._showxerr),
            (self._ybar, self._ycaps, self._showyerr),
        ):
            if bar is None:
                continue
            visible = self._visible and show
            bar.set_visible(visible)
            for cap in caps:
                cap.set_visible(visible)

    @GObject.Property(type=bool, default=True)
    def showxerr(self) -> bool:
        """Get showxerr property."""
        raise NotImplementedError

    @showxerr.setter
    def showxerr(self, showxerr: bool) -> None:
        """Set showxerr property."""
        self._showxerr = showxerr
        self._apply_visibility()

    @GObject.Property(type=bool, default=True)
    def showyerr(self) -> bool:
        """Get showyerr property."""
        raise NotImplementedError

    @showyerr.setter
    def showyerr(self, showyerr: bool) -> None:
        """Set showyerr property."""
        self._showyerr = showyerr
        self._apply_visibility()

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

    @GObject.Property(type=bool, default=True)
    def visible(self) -> bool:
        """Get visible property."""
        return self._visible

    @visible.setter
    def visible(self, visible: bool) -> None:
        """Set visible property."""
        self._visible = visible
        self._apply_visibility()

    def _set_properties(self, *_args) -> None:
        linewidth, markersize = self.props.linewidth, self.props.markersize
        if not self.props.selected:
            linewidth *= 0.35
            markersize *= 0.35
        self._data.set_linewidth(linewidth)
        self._data.set_markersize(markersize)

    @staticmethod
    def _handle_singularities(data: Graphs.DataHolder) -> tuple:
        """Adjust data to handle singularity jumps."""
        xdata = utilities.bytes_to_ndarray(data.get_xdata_b())
        ydata = utilities.bytes_to_ndarray(data.get_ydata_b())
        xerr = utilities.bytes_to_ndarray(data.get_xerr_b())
        yerr = utilities.bytes_to_ndarray(data.get_yerr_b())

        if len(xdata) < 2:
            return xdata, ydata, xerr, yerr

        # Detect singularities using Median Absolute Deviation
        grad = numpy.abs(numpy.gradient(ydata, xdata))
        median = numpy.median(grad)
        mad = median_abs_deviation(grad, scale="normal")

        if mad == 0:
            mad = (xdata[1] - xdata[0]) * 0.01

        threshold = median + 6 * mad
        sign_change = numpy.sign(ydata[:-1]) != numpy.sign(ydata[1:])
        mask = (grad[:-1] > threshold) & sign_change

        if not numpy.any(mask):
            return xdata, ydata, xerr, yerr

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

        xdata = xdata.copy()
        ydata = ydata.copy()
        xdata[bad_points] = numpy.nan
        ydata[bad_points] = numpy.nan

        if xerr is not None:
            xerr = xerr.copy()
            xerr[bad_points] = numpy.nan

        if yerr is not None:
            yerr = yerr.copy()
            yerr[bad_points] = numpy.nan

        return xdata, ydata, xerr, yerr

    def __init__(self, axis: pyplot.axis, item: Graphs.Item) -> None:
        super().__init__()
        self._axis = axis
        self._lod_timeout_id = None
        self.props.downsample = item.get_downsample()
        self._store(item.props.data)
        xdata, ydata, xerr, yerr = self._full
        self._artist = axis.errorbar(
            xdata,
            ydata,
            xerr=xerr,
            yerr=yerr,
            label=item.get_name(),
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
        self._color_artist = self._data

        # We iterate over bar and caps in assignments to handle all
        # combinations with error bars on either or both axes.
        bar_iter = iter(self._bars)
        cap_iter = iter(self._caps)
        self._xbar, self._xcaps = None, ()
        self._ybar, self._ycaps = None, ()

        if xerr is not None:
            self._xbar = next(bar_iter)
            self._xcaps = tuple(islice(cap_iter, 2))
        if yerr is not None:
            self._ybar = next(bar_iter)
            self._ycaps = tuple(islice(cap_iter, 2))

        self._visible = item.get_visible()
        self._showxerr = item.get_showxerr()
        self._showyerr = item.get_showyerr()
        self._apply_visibility()

        self.props.legend = item.get_legend()
        for prop in ("linewidth", "markersize", "selected"):
            self.set_property(prop, item.get_property(prop))
            self.connect(f"notify::{prop}", self._set_properties)
        self._set_properties()
        self._apply_lod()

        self.connect("notify::downsample", self._apply_lod)
        self._view_handler = \
            axis.callbacks.connect("xlim_changed", self._queue_lod)
        self._parent = axis.figure.parent
        self._resize_handler = None if self._parent is None else \
            self._parent.connect("resize", self._queue_lod)

    def disconnect_item(self) -> None:
        """Release the view and resize handlers on detach."""
        if self._lod_timeout_id is not None:
            GObject.source_remove(self._lod_timeout_id)
            self._lod_timeout_id = None
        if self._view_handler is not None:
            self._axis.callbacks.disconnect(self._view_handler)
            self._view_handler = None
        if self._resize_handler is not None:
            self._parent.disconnect(self._resize_handler)
            self._resize_handler = None


class EquationItemArtistWrapper(ItemArtistWrapper):
    """Wrapper for EquationItem."""

    __gtype_name__ = "GraphsEquationItemArtistWrapper"
    selected = GObject.Property(type=bool, default=True)
    linewidth = GObject.Property(type=float, default=3)
    legend = GObject.Property(type=bool, default=True)
    _singularities_cache = {}

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        super().__init__()

        equation = item.get_equation()
        self._expr = ast.sympify(equation)
        self._program = item.get_program()
        self._axis = axis
        self._view_change_timeout_id = None
        self._view_handler = \
            axis.callbacks.connect("xlim_changed", self._on_view_change)
        self._artist = axis.plot(
            [],
            [],
            label=item.get_name(),
            color=item.get_color(),
            alpha=item.get_alpha(),
            linestyle=misc.LINESTYLES[item.get_linestyle() + 1],
            marker="none",
        )[0]
        self._color_artist = self._artist
        self.props.legend = item.get_legend()
        for prop in ("linewidth", "selected"):
            self.set_property(prop, item.get_property(prop))
            self.connect(f"notify::{prop}", self._set_properties)

        self._equation_handler = \
            item.connect("notify::equation", self._on_equation_change)
        self._item = item

        self._set_properties(None, None)
        self._generate_data()

    def disconnect_item(self) -> None:
        """Release the view and item subscriptions on detach."""
        if self._view_change_timeout_id is not None:
            GObject.source_remove(self._view_change_timeout_id)
            self._view_change_timeout_id = None
        self._axis.callbacks.disconnect(self._view_handler)
        self._item.disconnect(self._equation_handler)

    def _timeout_callback(self) -> bool:
        self._view_change_timeout_id = None
        self._generate_data()
        return False

    def _on_view_change(self, *_args) -> None:
        """Debounced view change handler that generates data after delay."""
        if self._view_change_timeout_id is not None:
            GObject.source_remove(self._view_change_timeout_id)
        self._view_change_timeout_id = \
            GObject.timeout_add(100, self._timeout_callback)

    # We cannot have a Property of type Graphs.Ast
    def _on_equation_change(self, item, _pspec) -> None:
        equation = item.get_equation()
        self._singularities_cache = False
        self._expr = ast.sympify(equation)
        self._program = item.get_program()
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
        scale = Graphs.scale_from_string(self._axis.get_xscale())

        lower = Graphs.get_value_at_fraction(-1, x_start, x_stop, scale)
        upper = Graphs.get_value_at_fraction(2, x_start, x_stop, scale)

        holder = Graphs.math_tools_program_to_data(
            self._program,
            lower,
            upper,
            5000,
            scale,
        )
        data = utilities.get_xy_data(holder)
        singularities = self._find_singularities(lower, upper)
        if singularities:
            data = self._insert_singularity_points(data, singularities)

        self._artist.set_data(*data)
        if self._axis.figure.parent is not None:
            self._axis.figure.parent.queue_draw()

    def _find_singularities(self, lower, upper):
        cached = self._singularities_cache
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
        all_singularities = find_singularities(self._expr, misc.X, domain)

        self._singularities_cache = {
            "limits": (x_min, x_max),
            "singularities": all_singularities,
        }

        return {s for s in all_singularities if lower <= s <= upper}

    def _insert_singularity_points(self, data, singularities) -> tuple:
        """Insert NaN and infinite value points at singularities."""
        xdata, ydata = data
        singularities_arr = numpy.fromiter(sorted(singularities), dtype=float)
        indices = numpy.searchsorted(xdata, singularities_arr)

        n = len(xdata)
        triple_mask = (indices > 1) & (indices < n - 1)
        new_size = n + len(indices) + 2 * triple_mask.sum()

        ylim = self._axis.get_ylim()
        ylim_range = abs(ylim[1] - ylim[0])
        ydata_range = numpy.nanmax(ydata) - numpy.nanmin(ydata)
        inf_value = max(ylim_range * 1.5, ydata_range * 1.5) * 2
        epsilon = (xdata[1] - xdata[0]) * 0.01

        # shift indices due to previous insertions
        shifts = numpy.cumsum(1 + 2 * triple_mask) - (1 + 2 * triple_mask)
        target_indices = indices + shifts

        triple_idxs = indices[triple_mask]
        triple_targets = target_indices[triple_mask]
        triple_values = singularities_arr[triple_mask]

        data_mask = numpy.ones(new_size, dtype=bool)
        data_mask[target_indices] = False
        data_mask[triple_targets + 1] = False
        data_mask[triple_targets + 2] = False

        x_new = numpy.empty(new_size, dtype=float)
        y_new = numpy.empty(new_size, dtype=float)
        x_new[data_mask] = xdata
        y_new[data_mask] = ydata

        left = numpy.sign(ydata[triple_idxs - 1] - ydata[triple_idxs - 2])
        right = -numpy.sign(ydata[triple_idxs + 1] - ydata[triple_idxs])
        inf_values = inf_value + ydata[triple_idxs]

        x_new[triple_targets] = triple_values - epsilon
        x_new[triple_targets + 1] = numpy.nan
        x_new[triple_targets + 2] = triple_values + epsilon

        y_new[triple_targets] = left * inf_values
        y_new[triple_targets + 1] = numpy.nan
        y_new[triple_targets + 2] = right * inf_values

        single_targets = target_indices[~triple_mask]
        x_new[single_targets] = numpy.nan
        y_new[single_targets] = numpy.nan

        return x_new, y_new


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
            item.get_xanchor(),
            item.get_yanchor(),
            item.get_text(),
            label=item.get_name(),
            color=item.get_color(),
            alpha=item.get_alpha(),
            fontsize=item.get_size(),
            rotation=item.get_rotation(),
            clip_on=True,
        )
        self._color_artist = self._artist


class FillItemArtistWrapper(ItemArtistWrapper):
    """Wrapper for FillItem."""

    __gtype_name__ = "GraphsFillItemArtistWrapper"
    legend = GObject.Property(type=bool, default=False)

    def _as_tuple(self, holder: Graphs.FillHolder) -> tuple[numpy.ndarray]:
        return (
            utilities.bytes_to_ndarray(holder.get_xdata_b()),
            utilities.bytes_to_ndarray(holder.get_lower_b()),
            utilities.bytes_to_ndarray(holder.get_upper_b()),
        )

    @GObject.Property(type=Graphs.FillHolder, flags=2)
    def data(self) -> Graphs.FillHolder:
        """Write-only property, ignored."""

    @data.setter
    def data(self, data: Graphs.FillHolder) -> None:
        if self._item.is_view_based():
            return
        self._set_paths(*self._as_tuple(data))

    def __init__(self, axis: pyplot.axis, item: Graphs.Item):
        super().__init__()
        self._item = item
        self._axis = axis
        self._view_change_timeout_id = None
        self._view_key = None
        self._view_xdata = None

        self._dummy_axis = Figure().add_subplot()
        self._artist = axis.fill_between(
            *self._as_tuple(item.get_data()),
            label=item.get_name(),
            color=item.get_color(),
            alpha=item.get_alpha(),
        )
        self._color_artist = self._artist
        self._xlim_handler = \
            axis.callbacks.connect("xlim_changed", self._on_view_change)
        self._ylim_handler = \
            axis.callbacks.connect("ylim_changed", self._on_view_change)
        self._bounds_handler = item.connect(
            "bounds-changed",
            self._on_bounds_changed,
        )
        self.set_property("legend", item.get_property("legend"))
        self._on_bounds_changed()

    def disconnect_item(self) -> None:
        """Release the view and item subscriptions on detach."""
        if self._view_change_timeout_id is not None:
            GObject.source_remove(self._view_change_timeout_id)
            self._view_change_timeout_id = None
        self._axis.callbacks.disconnect(self._xlim_handler)
        self._axis.callbacks.disconnect(self._ylim_handler)
        self._item.disconnect(self._bounds_handler)

    def _clamp(self, ydata: numpy.ndarray) -> numpy.ndarray:
        """Resolve infinities to the edge of the visible area."""
        if numpy.all(numpy.isfinite(ydata)):
            return ydata
        low, high = sorted(self._axis.get_ylim())
        span = high - low
        return numpy.clip(ydata, low - span, high + span)

    def _set_paths(self, xdata, lower, upper) -> None:
        collection = self._dummy_axis.fill_between(
            xdata,
            self._clamp(lower),
            self._clamp(upper),
        )

        paths = collection.get_paths()
        collection.remove()
        if not paths:
            return
        self._artist.set_paths([paths[0].vertices])
        self._axis.figure.queue_draw()

    def _generate_from_view(self) -> None:
        """Sample the equation bounds across the visible range."""
        x_start, x_stop = self._axis.get_xlim()
        scale = Graphs.scale_from_string(self._axis.get_xscale())

        # recalculate xdata if view has changed
        key = (x_start, x_stop, scale)
        if key != self._view_key:
            self._view_xdata = numpy.array([
                Graphs.get_value_at_fraction(fraction, x_start, x_stop, scale)
                for fraction in numpy.linspace(-1, 2, 5000)
            ])
            self._view_key = key

        lower, upper = self._item.evaluate_bounds(self._view_xdata)
        self._set_paths(self._view_xdata, lower, upper)

    def _on_bounds_changed(self, *_args) -> None:
        """Redraw after a bound changed, whichever kind it now is."""
        if self._item.is_view_based():
            self._generate_from_view()
        else:
            self._set_paths(*self._as_tuple(self._item.get_data()))

    def _timeout_callback(self) -> bool:
        self._view_change_timeout_id = None
        self._on_bounds_changed()
        return False

    def _on_view_change(self, *_args) -> None:
        """Debounced view change handler that redraws after a delay."""
        if self._view_change_timeout_id is not None:
            GObject.source_remove(self._view_change_timeout_id)
        self._view_change_timeout_id = \
            GObject.timeout_add(100, self._timeout_callback)
