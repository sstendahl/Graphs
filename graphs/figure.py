# SPDX-License-Identifier: GPL-3.0-or-later
"""
Custom figure implementation.

Acts as an interface between matplotlib and GObject.
"""
import contextlib
import logging
from typing import Tuple

from gi.repository import GObject, Gio, Gtk

from graphs import artist, misc, scales

from matplotlib import RcParams, figure, pyplot


class Figure(GObject.Object, figure.Figure):
    """Custom Figure."""

    __gtype_name__ = "GraphsFigure"

    def __init__(
        self,
        style_params: Tuple[RcParams, dict],
        items: Gio.ListModel,
        parent=None,
    ):
        GObject.Object.__init__(self)
        self._style_params = style_params
        self._items = items
        self.parent = parent
        pyplot.rcParams.update(self._style_params[0])  # apply style_params
        figure.Figure.__init__(self, tight_layout=True)

        self.axis = self.add_subplot(111)
        self.top_left_axis = self.axis.twiny()
        self.right_axis = self.axis.twinx()
        self.top_right_axis = self.top_left_axis.twinx()
        self._hide_unselected = False
        self._legend_axis = self.axis
        self._legend = True
        self._legend_position = misc.LEGEND_POSITIONS[0]
        self._artists = []

        items.connect("items-changed", self._redraw)
        if isinstance(items, Gtk.SelectionModel):
            items.connect("selection-changed", self._redraw)
        self._redraw()

    def _redraw(self, *_args) -> None:
        logging.debug("redrawing figure")
        # bottom, top, left, right
        used_axes = [False, False, False, False]
        visible_axes = [False, False, False, False]
        drawable_items = [x for x in self._items if x.get_selected()] \
            if self._hide_unselected else list(self._items)
        for item in drawable_items:
            xposition = item.get_xposition()
            yposition = item.get_yposition()
            visible_axes[xposition] = True
            visible_axes[2 + yposition] = True
            used_axes[xposition + 2 * yposition] = True
        axes_directions = (
            ("bottom", "left"),  # axis
            ("top", "left"),  # top_left_axis
            ("bottom", "right"),  # right_axis
            ("top", "right"),  # top_right_axis
        )

        if not any(visible_axes):
            visible_axes = (True, False, True, False)  # Left and bottom
            used_axes = (True, False, False, False)  # self.axis visible
            self._legend_axis = self.axis

        params, graphs_params = self._style_params
        draw_frame = params["axes.spines.bottom"]
        ticks = "both" if params["xtick.minor.visible"] else "major"
        for directions, axis, used \
                in zip(axes_directions, self.axes, used_axes):
            axis.get_xaxis().set_visible(False)
            axis.get_yaxis().set_visible(False)
            # Set tick where requested, as long as that axis is not occupied
            # and visible
            if (
                params[f"xtick.{directions[0]}"]
                or params[f"ytick.{directions[1]}"]
            ):
                tick_params = {}
                for i, direction in enumerate(misc.DIRECTIONS):
                    tick_shown = (
                        (draw_frame and not visible_axes[i])
                        or direction in directions
                    ) and params[f"{'x' if i < 2 else 'y'}tick.{direction}"]

                    tick_params[direction] = tick_shown
                    if graphs_params["ticklabels"]:
                        tick_params[f"label{direction}"] = tick_shown

                axis.tick_params(which=ticks, **tick_params)

            for handle in axis.lines + axis.texts:
                handle.remove()
            axis_legend = axis.get_legend()
            if axis_legend is not None:
                axis_legend.remove()
            for direction in misc.DIRECTIONS:
                axis.spines[direction].set_visible(
                    direction in directions and used or draw_frame,
                )
            if used:
                self._legend_axis = axis

        self.axis.get_xaxis().set_visible(visible_axes[0])
        self.top_left_axis.get_xaxis().set_visible(visible_axes[1])
        self.axis.get_yaxis().set_visible(visible_axes[2])
        self.right_axis.get_yaxis().set_visible(visible_axes[3])

        self._artists = [
            artist.new_for_item(self, item)
            for item in reversed(drawable_items)
        ]
        self.update_legend()

    def update_legend(self) -> None:
        """Update the legend or hide if not used."""
        if self._legend and self._artists:
            handles = [
                handle.get_artist() for handle in self._artists
                if handle.legend
            ]
            if handles:
                self._legend_axis.legend(
                    handles=handles,
                    loc=self._legend_position,
                    frameon=True,
                    reverse=True,
                )
                self.queue_draw()
                return
        legend = self._legend_axis.get_legend()
        if legend is not None:
            legend.remove()
        self.queue_draw()

    def set_properties(*args):
        """Pass method on to Figure."""
        figure.Figure.set_properties(*args)

    def set_property(*args):
        """Pass method on to Figure."""
        figure.Figure.set_property(*args)

    def queue_draw(self) -> None:
        """Queue a draw when in a canvas."""
        with contextlib.suppress(AttributeError):
            self.canvas.queue_draw()

    @GObject.Property(type=bool, default=False)
    def hide_unselected(self) -> bool:
        """Whether or not to hide unselected items."""
        return self._hide_unselected

    @hide_unselected.setter
    def hide_unselected(self, hide_unselected: bool) -> None:
        self._hide_unselected = hide_unselected
        self._redraw()

    @GObject.Property(type=bool, default=True)
    def legend(self) -> bool:
        """Whether or not, the legend is visible."""
        return self._legend

    @legend.setter
    def legend(self, legend: bool) -> None:
        self._legend = legend
        self.update_legend()

    @GObject.Property(type=int, default=0)
    def legend_position(self) -> int:
        """Legend Position (see `misc.LEGEND_POSITIONS`)."""
        return misc.LEGEND_POSITIONS.index(self._legend_position)

    @legend_position.setter
    def legend_position(self, legend_position: int) -> None:
        self._legend_position = misc.LEGEND_POSITIONS[legend_position]
        self.update_legend()

    @GObject.Property(type=str)
    def title(self) -> str:
        """Figure title."""
        return self.axis.get_title()

    @title.setter
    def title(self, title: str) -> None:
        self.axis.set_title(title, picker=True).id = "title"
        self.queue_draw()

    @GObject.Property(type=str)
    def bottom_label(self) -> str:
        """Label of the bottom axis."""
        return self.axis.get_xlabel()

    @bottom_label.setter
    def bottom_label(self, label: str) -> None:
        self.axis.set_xlabel(label, picker=True).id = "bottom_label"
        self.queue_draw()

    @GObject.Property(type=str)
    def left_label(self) -> str:
        """Label of the left axis."""
        return self.axis.get_ylabel()

    @left_label.setter
    def left_label(self, label: str) -> None:
        self.axis.set_ylabel(label, picker=True).id = "left_label"
        self.queue_draw()

    @GObject.Property(type=str)
    def top_label(self) -> str:
        """Label of the top axis."""
        return self.top_left_axis.get_xlabel()

    @top_label.setter
    def top_label(self, label: str) -> None:
        self.top_left_axis.set_xlabel(label, picker=True).id = "top_label"
        self.queue_draw()

    @GObject.Property(type=str)
    def right_label(self) -> str:
        """Label of the right axis."""
        return self.right_axis.get_ylabel()

    @right_label.setter
    def right_label(self, label: str) -> None:
        self.right_axis.set_ylabel(label, picker=True).id = "right_label"
        self.queue_draw()

    @GObject.Property(type=int)
    def bottom_scale(self) -> int:
        """Scale of the bottom axis."""
        return scales.Scale.from_string(self.axis.get_xscale()).value

    @bottom_scale.setter
    def bottom_scale(self, scale: int) -> None:
        scale = scales.Scale(scale).to_string()
        for axis in (self.axis, self.right_axis):
            axis.set_xscale(scale)
            axis.set_xlim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def left_scale(self) -> int:
        """Scale of the left axis."""
        return scales.Scale.from_string(self.axis.get_yscale()).value

    @left_scale.setter
    def left_scale(self, scale: int) -> None:
        scale = scales.Scale(scale).to_string()
        for axis in (self.axis, self.top_left_axis):
            axis.set_yscale(scale)
            axis.set_ylim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def top_scale(self) -> int:
        """Scale of the top axis."""
        return scales.Scale.from_string(self.top_left_axis.get_xscale()).value

    @top_scale.setter
    def top_scale(self, scale: int) -> None:
        scale = scales.Scale(scale).to_string()
        for axis in (self.top_right_axis, self.top_left_axis):
            axis.set_xscale(scale)
            axis.set_xlim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def right_scale(self) -> int:
        """Scale of the right axis."""
        return scales.Scale.from_string(self.right_axis.get_yscale()).value

    @right_scale.setter
    def right_scale(self, scale: int) -> None:
        scale = scales.Scale(scale).to_string()
        for axis in (self.top_right_axis, self.right_axis):
            axis.set_yscale(scale)
            axis.set_ylim(None, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_bottom(self) -> float:
        """Lower limit for the bottom axis."""
        return self.axis.get_xlim()[0]

    @min_bottom.setter
    def min_bottom(self, value: float) -> None:
        for axis in (self.axis, self.right_axis):
            axis.set_xlim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_bottom(self) -> float:
        """Upper limit for the bottom axis."""
        return self.axis.get_xlim()[1]

    @max_bottom.setter
    def max_bottom(self, value: float) -> None:
        for axis in (self.axis, self.right_axis):
            axis.set_xlim(None, value)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_left(self) -> float:
        """Lower limit for the left axis."""
        return self.axis.get_ylim()[0]

    @min_left.setter
    def min_left(self, value: float) -> None:
        for axis in (self.axis, self.top_left_axis):
            axis.set_ylim(value, None)

    @GObject.Property(type=float)
    def max_left(self) -> float:
        """Upper limit for the left axis."""
        return self.axis.get_ylim()[1]

    @max_left.setter
    def max_left(self, value: float) -> None:
        for axis in (self.axis, self.top_left_axis):
            axis.set_ylim(None, value)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_top(self) -> float:
        """Lower limit for the top axis."""
        return self.top_left_axis.get_xlim()[0]

    @min_top.setter
    def min_top(self, value: float) -> None:
        for axis in (self.top_left_axis, self.top_right_axis):
            axis.set_xlim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_top(self) -> float:
        """Upper limit for the top axis."""
        return self.top_left_axis.get_xlim()[1]

    @max_top.setter
    def max_top(self, value: float) -> None:
        for axis in (self.top_left_axis, self.top_right_axis):
            axis.set_xlim(None, value)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_right(self) -> float:
        """Lower limit for the right axis."""
        return self.right_axis.get_ylim()[0]

    @min_right.setter
    def min_right(self, value: float) -> None:
        for axis in (self.right_axis, self.top_right_axis):
            axis.set_ylim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_right(self) -> float:
        """Upper limit for the right axis."""
        return self.right_axis.get_ylim()[1]

    @max_right.setter
    def max_right(self, value: float) -> None:
        for axis in (self.right_axis, self.top_right_axis):
            axis.set_ylim(None, value)
        self.queue_draw()
