# SPDX-License-Identifier: GPL-3.0-or-later
"""
Custom canvas implementation.

Acts as an interface between matplotlib and GObject and contains a custom
implementation of a `SpanSelector` as well as a dummy toolbar used for
interactive navigation in conjunction with graphs-specific structures.

    Classes:
        Canvas
"""
import logging
import math

from gi.repository import Adw, GObject, Gdk, Gio, Graphs, Gtk

import gio_pyio

from graphs import artist, misc, scales, utilities

from matplotlib import backend_tools as tools, pyplot
from matplotlib.backend_bases import (
    FigureCanvasBase,
    MouseEvent,
    NavigationToolbar2,
)
from matplotlib.backends.backend_gtk4cairo import FigureCanvas
from matplotlib.widgets import SpanSelector

_SCROLL_SCALE = 1.06


class Canvas(Graphs.Canvas, FigureCanvas):
    """
    Custom Canvas.

    Implements properties analouge to `FigureSettings`. Automatically connects
    to `FigureSettings` and `Data.items` during init.

    Properties:
        mode: int

        items: list (write-only)

        title: str
        bottom_label: str
        left_label: str
        top_label: str
        right_label: str

        bottom_scale: int (0: linear, 1: logarithmic)
        left_scale: int (0: linear, 1: logarithmic)
        top_scale: int (0: linear, 1: logarithmic)
        right_scale: int (0: linear, 1: logarithmic)

        legend: bool
        legend_position: int
        use_custom_style: bool
        custom_style: str

        min_bottom: float
        max_bottom: float
        min_left: float
        max_lef: float
        min_top: float
        max_top: float
        min_right: float
        max_right: float

        min_selected: float (fraction)
        max_selected: float (fraction)

    Signals:
        edit_request
        view_changed

    Functions:
        update_legend
    """

    __gtype_name__ = "GraphsPythonCanvas"

    def __init__(
        self,
        style_params: dict,
        items: Gio.ListModel,
        interactive: bool = True,
    ):
        """
        Create the canvas.

        Create figure, axes and define rubberband_colors based on the current
        style context. Bind `items` to `data.items` and all figure settings
        attributes to their respective values.
        """
        self._style_params = style_params
        pyplot.rcParams.update(self._style_params)  # apply style_params
        Graphs.Canvas.__init__(
            self,
            hexpand=True,
            vexpand=True,
            items=items,
        )
        self._idle_draw_id = 0
        self.set_draw_func(self._draw_func)
        self.connect("resize", self.resize_event)
        self.connect("notify::scale-factor", self._update_device_pixel_ratio)
        FigureCanvasBase.__init__(self)
        self.figure.set_tight_layout(True)
        self._axis = self.figure.add_subplot(111)
        self._top_left_axis = self._axis.twiny()
        self._right_axis = self._axis.twinx()
        self._top_right_axis = self._top_left_axis.twinx()
        self.axes = [
            self._axis,
            self._top_left_axis,
            self._right_axis,
            self._top_right_axis,
        ]
        self._legend_axis = self._axis
        self._legend = True
        self._legend_position = misc.LEGEND_POSITIONS[0]
        self._handles = []
        self._rubberband_rect = None

        # Handle stuff only used if the canvas is interactive
        if interactive:
            self._setup_interactive()

        self.connect("save-request", self._save)
        self.connect(
            "zoom_request",
            lambda _self, factor: self.zoom(factor, False),
        )

        self.connect("notify::hide-unselected", self._redraw)
        items.connect("items-changed", self._redraw)
        if isinstance(items, Gtk.SelectionModel):
            items.connect("selection-changed", self._redraw)
        self._redraw()

    def _setup_interactive(self):
        self._ctrl_held, self._shift_held = False, False
        self._xfrac, self._yfrac = None, None
        self.mpl_connect("pick_event", self._on_pick)
        self.mpl_connect("motion_notify_event", self._set_mouse_fraction)
        self._make_ticklabels_pickable()

        # Reference is created by the toolbar itself
        _DummyToolbar(self)

        click = Gtk.GestureClick()
        click.set_button(0)  # All buttons.
        click.connect("pressed", self.button_press_event)
        click.connect("update", self.handle_touch_update)
        click.connect("released", self.button_release_event)
        self.add_controller(click)

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self.motion_notify_event)
        motion.connect("enter", self.enter_notify_event)
        motion.connect("leave", self.leave_notify_event)
        self.add_controller(motion)

        scroll = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.BOTH_AXES,
        )
        scroll.connect("scroll", self.scroll_event)
        scroll.connect("scroll-end", self.toolbar.push_current)
        self.add_controller(scroll)

        zoom = Gtk.GestureZoom.new()
        zoom.connect("scale-changed", self.zoom_event)
        zoom.connect("end", self.end_zoom_event)
        self.add_controller(zoom)

        def rgba_to_tuple(rgba):
            return (rgba.red, rgba.green, rgba.blue, rgba.alpha)

        style_manager = Adw.StyleManager()
        rgba = style_manager.get_accent_color_rgba()
        self.rubberband_edge_color = rgba_to_tuple(rgba)
        rgba.alpha = 0.2
        self.rubberband_fill_color = rgba_to_tuple(rgba)
        self.highlight = _Highlight(self)
        self.connect("notify::mode", self._on_mode_change)
        self._on_mode_change()

        for item in ("min", "max"):
            self.connect(
                f"notify::{item}-selected",
                lambda _a,
                _b: self.highlight.load(self),
            )

    def _make_ticklabels_pickable(self) -> None:
        """Make all tick labels pickable."""
        for ax in self.axes:
            for label in (ax.get_xticklabels() + ax.get_yticklabels()):
                label.set_picker(True)

    def handle_touch_update(self, controller: Gtk.GestureClick, _data) -> None:
        """
        Handle an update event for GtkGestureClick motion.

        This is needed for touch screen devices to handle gestures properly.
        """
        if not controller.get_point()[0]:  # If touch event
            coords = controller.get_bounding_box_center()
            x, y = coords.x, coords.y
            MouseEvent(
                "motion_notify_event",
                self,
                *self._mpl_coords((x, y)),
            )._process()

    def key_press_event(
        self,
        controller: Gtk.EventControllerKey,
        keyval: int,
        keycode: int,
        state: Gdk.ModifierType,
    ) -> None:
        """Handle key press event."""
        if keyval in {65507, 65508}:  # Control_L or Control_R
            self._ctrl_held = True
        elif keyval in {65505, 65506}:  # Left or right Shift
            self._shift_held = True
        else:  # Prevent keys from being true with key combos
            self._ctrl_held = False
        super().key_press_event(controller, keyval, keycode, state)

    def key_release_event(
        self,
        controller: Gtk.EventControllerKey,
        keyval: int,
        keycode: int,
        state: Gdk.ModifierType,
    ) -> None:
        """Handle key release event."""
        self._ctrl_held = False
        self._shift_held = False
        super().key_release_event(controller, keyval, keycode, state)

    def scroll_event(
        self,
        controller: Gtk.EventControllerScroll,
        dx: float,
        dy: float,
    ) -> None:
        """Handle scroll event."""
        if self._ctrl_held:
            self.zoom(1 / _SCROLL_SCALE if dy > 0 else _SCROLL_SCALE)
        else:
            if self._shift_held:
                dx, dy = dy, dx
            if controller.get_unit() == Gdk.ScrollUnit.WHEEL:
                dx *= 10
                dy *= 10
            for ax in self.axes:
                xmin, xmax, ymin, ymax = \
                    self._calculate_pan_values(ax, dx, dy)
                ax.set_xlim(xmin, xmax)
                ax.set_ylim(ymin, ymax)
        self.toolbar.push_current()
        super().scroll_event(controller, dx, dy)

    def zoom_event(
        self,
        controller: Gtk.GestureZoom,
        scale: float,
    ) -> None:
        """Handle zoom event."""
        coords = controller.get_bounding_box_center()
        x, y = coords.x, coords.y
        event = MouseEvent(
            "motion_notify_event",
            self,
            *self._mpl_coords((x, y)),
        )
        self._set_mouse_fraction(event)

        scale = 1 + 0.01 * (scale - 1)
        if scale > 5 or scale < 0.2:
            # Don't scale if ridiculous values are registered
            return
        self.zoom(scale)

    def end_zoom_event(self, controller: Gtk.GestureZoom, _sequence) -> None:
        """
        End the zoom event.

        Pushes the canvas to the stack, and emits a `release` signal cancel out
        registered touches from touchscreen devices.
        """
        coords = controller.get_bounding_box_center()
        x, y = coords.x, coords.y
        MouseEvent(
            "button_release_event",
            self,
            *self._mpl_coords((x, y)),
            1,
        )._process()
        self.toolbar.push_current()

    def enter_notify_event(
        self,
        controller: Gtk.EventControllerMotion,
        x: float,
        y: float,
    ) -> None:
        """Process pointer entry."""
        self.grab_focus()
        super().enter_notify_event(controller, x, y)

    def _set_mouse_fraction(self, event) -> None:
        """Set the mouse coordinate in terms of fraction of the canvas."""
        if event.inaxes is not None:
            xlim = self._top_right_axis.get_xlim()
            ylim = self._top_right_axis.get_ylim()
            self._xfrac = utilities.get_fraction_at_value(
                event.xdata,
                xlim[0],
                xlim[1],
                self.top_scale,
            )
            self._yfrac = utilities.get_fraction_at_value(
                event.ydata,
                ylim[0],
                ylim[1],
                self.right_scale,
            )
        else:
            self._xfrac, self._yfrac = None, None

    def zoom(self, scaling: float = 1.15, respect_mouse: bool = True) -> None:
        """
        Zoom with given scaling.

        Update all axes' limits in respect to the current mouse position.
        """
        if not respect_mouse:
            self._xfrac, self._yfrac = 0.5, 0.5
        if self._xfrac is None or self._yfrac is None:
            return
        for ax in self.axes:
            ax.set_xlim(
                self._calculate_zoomed_values(
                    self._xfrac,
                    scales.Scale.from_string(ax.get_xscale()),
                    ax.get_xlim(),
                    scaling,
                ),
            )
            ax.set_ylim(
                self._calculate_zoomed_values(
                    self._yfrac,
                    scales.Scale.from_string(ax.get_yscale()),
                    ax.get_ylim(),
                    scaling,
                ),
            )
        self.queue_draw()

    @staticmethod
    def _calculate_pan_values(
        ax: pyplot.axis,
        x_panspeed: float,
        y_panspeed: float,
    ) -> None:
        """
        Calculate values required for panning.

        Calculates the coordinates of the canvas after a panning gesture has
        been emitted.
        """
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        x_scale = scales.Scale.from_string(ax.get_xscale())
        y_scale = scales.Scale.from_string(ax.get_yscale())
        pan_scale = 0.002
        xvalue1 = utilities.get_value_at_fraction(
            x_panspeed * pan_scale,
            xmin,
            xmax,
            x_scale.value,
        )
        xvalue2 = utilities.get_value_at_fraction(
            1 + x_panspeed * pan_scale,
            xmin,
            xmax,
            x_scale.value,
        )
        yvalue1 = utilities.get_value_at_fraction(
            -y_panspeed * pan_scale,
            ymin,
            ymax,
            y_scale.value,
        )
        yvalue2 = utilities.get_value_at_fraction(
            1 - y_panspeed * pan_scale,
            ymin,
            ymax,
            y_scale.value,
        )
        if x_scale == scales.Scale.INVERSE:
            xvalue1, xvalue2 = xvalue2, xvalue1
        if y_scale == scales.Scale.INVERSE:
            yvalue1, yvalue2 = yvalue2, yvalue1
        return xvalue1, xvalue2, yvalue1, yvalue2

    @staticmethod
    def _calculate_zoomed_values(
        fraction: float,
        scale: scales.Scale,
        limit: float,
        zoom_factor: float,
    ) -> tuple[float, float]:
        """
        Calculate zoomed values.

        Calculates the coordinates of the canvas after a zoom gesture
        has  been ezoomed.
        """
        min_, max_ = limit[0], limit[1]
        value1 = utilities.get_value_at_fraction(
            fraction - fraction / zoom_factor,
            min_,
            max_,
            scale.value,
        )
        value2 = utilities.get_value_at_fraction(
            fraction + (1 - fraction) / zoom_factor,
            min_,
            max_,
            scale.value,
        )
        if scale == scales.Scale.INVERSE:
            value1, value2 = value2, value1
        return value1, value2

    def _redraw(self, *_args) -> None:
        logging.debug("redrawing canvas")
        # bottom, top, left, right
        used_axes = [False, False, False, False]
        visible_axes = [False, False, False, False]
        drawable_items = [x for x in self.props.items if x.get_selected()] \
            if self.props.hide_unselected else list(self.props.items)
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
            self._legend_axis = self._axis

        params = self._style_params
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
                axis.tick_params(
                    which=ticks,
                    **{
                        direction: (
                            draw_frame and not visible_axes[i]
                            or direction in directions
                        )
                        and params[f"{'x' if i < 2 else 'y'}tick.{direction}"]
                        for i,
                        direction in enumerate(misc.DIRECTIONS)
                    },
                )
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

        self._axis.get_xaxis().set_visible(visible_axes[0])
        self._top_left_axis.get_xaxis().set_visible(visible_axes[1])
        self._axis.get_yaxis().set_visible(visible_axes[2])
        self._right_axis.get_yaxis().set_visible(visible_axes[3])

        self._handles = [
            artist.new_for_item(self, item)
            for item in reversed(drawable_items)
        ]
        self.update_legend()

    def _on_pick(self, event) -> None:
        """Emit edit-request signal for picked label, tick or title."""
        artist = event.artist

        if not hasattr(artist, "id"):
            artist.id = self._determine_artist_id(artist)

        self.emit("edit_request", artist.id)

    def _determine_artist_id(self, artist) -> str:
        """
        Determine the tick artist id based on its position.

        Determines the artist's position to generate an artist id that matches
        with the appropriate limits-widget figure_settings.

        The artist position is a tuple where one element is an integer (0 or 1)
        indicating the axis side, and the other is a numpy float indicating the
        value of the clicked tick.
        The position of the integer determines the axis:
        - Integer at index 0: X-axis (0=left, 1=right)
        - Integer at index 1: Y-axis (0=bottom, 1=top)
        """
        artist_position = artist.get_position()

        # X axis
        if isinstance(artist_position[0], int):
            position, label_value = artist_position
            side = "left" if position == 0 else "right"

        # Y-axis
        elif isinstance(artist_position[1], int):
            label_value, position = artist_position
            side = "bottom" if position == 0 else "top"

        min_val = getattr(self, f"min_{side}", None)
        max_val = getattr(self, f"max_{side}", None)
        midpoint = (min_val + max_val) / 2
        position_type = "max" if label_value > midpoint else "min"

        return f"{position_type}_{side}"

    # Overwritten function - do not change name
    def _post_draw(self, _widget, context) -> None:
        """Allow custom rendering extensions."""
        if self._rubberband_rect is not None:
            self._draw_rubberband(context)

    def _draw_rubberband(self, ctx) -> None:
        """
        Implement custom rubberband.

        Draw a rubberband matching libadwaitas style, where `_rubberband_rect`
        is set.
        """
        radius = 6
        x0, y0, width, height = (
            dim / self.device_pixel_ratio for dim in self._rubberband_rect
        )
        x1 = x0 + width
        y1 = y0 + height

        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0

        degrees = math.pi / 180

        ctx.new_sub_path()
        ctx.arc(x1 - radius, y0 + radius, radius, -90 * degrees, 0 * degrees)
        ctx.arc(x1 - radius, y1 - radius, radius, 0 * degrees, 90 * degrees)
        ctx.arc(x0 + radius, y1 - radius, radius, 90 * degrees, 180 * degrees)
        ctx.arc(x0 + radius, y0 + radius, radius, 180 * degrees, 270 * degrees)
        ctx.close_path()

        ctx.set_line_width(1)
        ctx.set_source_rgba(*self.rubberband_fill_color)
        ctx.fill_preserve()
        ctx.set_source_rgba(*self.rubberband_edge_color)
        ctx.stroke()

    def update_legend(self) -> None:
        """Update the legend or hide if not used."""
        if self._legend and self._handles:
            handles = [
                handle.get_artist() for handle in self._handles
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

    @staticmethod
    def _save(
        self,
        file: Gio.File,
        fmt: str,
        dpi: int,
        transparent: bool,
    ) -> None:
        with gio_pyio.open(file, "wb") as file_like:
            self.figure.savefig(
                file_like,
                format=fmt,
                dpi=dpi,
                transparent=transparent,
            )

    def _on_mode_change(self, *_args) -> None:
        highlight_enabled = self.props.mode == 2
        self.highlight.set_active(highlight_enabled)
        self.highlight.set_visible(highlight_enabled)
        self.queue_draw()

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
        return self._axis.get_title()

    @title.setter
    def title(self, title: str) -> None:
        self._axis.set_title(title, picker=True).id = "title"
        self.queue_draw()

    @GObject.Property(type=str)
    def bottom_label(self) -> str:
        """Label of the bottom axis."""
        return self._axis.get_xlabel()

    @bottom_label.setter
    def bottom_label(self, label: str) -> None:
        self._axis.set_xlabel(label, picker=True).id = "bottom_label"
        self.queue_draw()

    @GObject.Property(type=str)
    def left_label(self) -> str:
        """Label of the left axis."""
        return self._axis.get_ylabel()

    @left_label.setter
    def left_label(self, label: str) -> None:
        self._axis.set_ylabel(label, picker=True).id = "left_label"
        self.queue_draw()

    @GObject.Property(type=str)
    def top_label(self) -> str:
        """Label of the top axis."""
        return self._top_left_axis.get_xlabel()

    @top_label.setter
    def top_label(self, label: str) -> None:
        self._top_left_axis.set_xlabel(label, picker=True).id = "top_label"
        self.queue_draw()

    @GObject.Property(type=str)
    def right_label(self) -> str:
        """Label of the right axis."""
        return self._right_axis.get_ylabel()

    @right_label.setter
    def right_label(self, label: str) -> None:
        self._right_axis.set_ylabel(label, picker=True).id = "right_label"
        self.queue_draw()

    @GObject.Property(type=int)
    def bottom_scale(self) -> int:
        """Scale of the bottom axis."""
        return scales.Scale.from_string(self._axis.get_xscale()).value

    @bottom_scale.setter
    def bottom_scale(self, scale: int) -> None:
        scale = scales.Scale(scale).to_string()
        for axis in (self._axis, self._right_axis):
            axis.set_xscale(scale)
            axis.set_xlim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def left_scale(self) -> int:
        """Scale of the left axis."""
        return scales.Scale.from_string(self._axis.get_yscale()).value

    @left_scale.setter
    def left_scale(self, scale: int) -> None:
        scale = scales.Scale(scale).to_string()
        for axis in (self._axis, self._top_left_axis):
            axis.set_yscale(scale)
            axis.set_ylim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def top_scale(self) -> int:
        """Scale of the top axis."""
        return scales.Scale.from_string(self._top_left_axis.get_xscale()).value

    @top_scale.setter
    def top_scale(self, scale: int) -> None:
        scale = scales.Scale(scale).to_string()
        for axis in (self._top_right_axis, self._top_left_axis):
            axis.set_xscale(scale)
            axis.set_xlim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def right_scale(self) -> int:
        """Scale of the right axis."""
        return scales.Scale.from_string(self._right_axis.get_yscale()).value

    @right_scale.setter
    def right_scale(self, scale: int) -> None:
        scale = scales.Scale(scale).to_string()
        for axis in (self._top_right_axis, self._right_axis):
            axis.set_yscale(scale)
            axis.set_ylim(None, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_bottom(self) -> float:
        """Lower limit for the bottom axis."""
        return self._axis.get_xlim()[0]

    @min_bottom.setter
    def min_bottom(self, value: float) -> None:
        for axis in (self._axis, self._right_axis):
            axis.set_xlim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_bottom(self) -> float:
        """Upper limit for the bottom axis."""
        return self._axis.get_xlim()[1]

    @max_bottom.setter
    def max_bottom(self, value: float) -> None:
        for axis in (self._axis, self._right_axis):
            axis.set_xlim(None, value)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_left(self) -> float:
        """Lower limit for the left axis."""
        return self._axis.get_ylim()[0]

    @min_left.setter
    def min_left(self, value: float) -> None:
        for axis in (self._axis, self._top_left_axis):
            axis.set_ylim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_left(self) -> float:
        """Upper limit for the left axis."""
        return self._axis.get_ylim()[1]

    @max_left.setter
    def max_left(self, value: float) -> None:
        for axis in (self._axis, self._top_left_axis):
            axis.set_ylim(None, value)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_top(self) -> float:
        """Lower limit for the top axis."""
        return self._top_left_axis.get_xlim()[0]

    @min_top.setter
    def min_top(self, value: float) -> None:
        for axis in (self._top_left_axis, self._top_right_axis):
            axis.set_xlim(value, None)
        self.highlight.load(self)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_top(self) -> float:
        """Upper limit for the top axis."""
        return self._top_left_axis.get_xlim()[1]

    @max_top.setter
    def max_top(self, value: float) -> None:
        for axis in (self._top_left_axis, self._top_right_axis):
            axis.set_xlim(None, value)
        self.highlight.load(self)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_right(self) -> float:
        """Lower limit for the right axis."""
        return self._right_axis.get_ylim()[0]

    @min_right.setter
    def min_right(self, value: float) -> None:
        for axis in (self._right_axis, self._top_right_axis):
            axis.set_ylim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_right(self) -> float:
        """Upper limit for the right axis."""
        return self._right_axis.get_ylim()[1]

    @max_right.setter
    def max_right(self, value: float) -> None:
        for axis in (self._right_axis, self._top_right_axis):
            axis.set_ylim(None, value)
        self.queue_draw()


class _DummyToolbar(NavigationToolbar2):
    """Custom Toolbar implementation."""

    # Overwritten function - do not change name
    def _zoom_pan_handler(self, event) -> None:
        mode = self.canvas.props.mode
        if event.button == 2:
            event.button = 1
            mode = 0
        elif event.button != 1:
            return
        if mode == 0:
            if event.name == "button_press_event":
                self.press_pan(event)
            elif event.name == "button_release_event":
                self.release_pan(event)
        elif mode == 1:
            if event.name == "button_press_event":
                self.press_zoom(event)
            elif event.name == "button_release_event":
                self.release_zoom(event)

    # Overwritten function - do not change name
    def _update_cursor(self, event) -> None:
        mode = self.canvas.props.mode
        if event.inaxes and event.inaxes.get_navigate():
            if mode == 1 and self._last_cursor != tools.Cursors.SELECT_REGION:
                self.canvas.set_cursor(tools.Cursors.SELECT_REGION)
                self._last_cursor = tools.Cursors.SELECT_REGION
            elif mode == 0 and self._last_cursor != tools.Cursors.MOVE:
                self.canvas.set_cursor(tools.Cursors.MOVE)
                self._last_cursor = tools.Cursors.MOVE
        elif self._last_cursor != tools.Cursors.POINTER:
            self.canvas.set_cursor(tools.Cursors.POINTER)
            self._last_cursor = tools.Cursors.POINTER

    # Overwritten function - do not change name
    def drag_pan(self, event):
        """Handle dragging in pan/zoom mode."""
        for ax in self._pan_info.axes:
            # Using the recorded button at the press is safer than the current
            # button, as multiple buttons can get pressed during motion.
            # Use custom drag_pan that maxes sure limits are set in right order
            # even on inverted scale
            self.ax_drag_pan(
                ax,
                self._pan_info.button,
                event.key,
                event.x,
                event.y,
            )
        self.canvas.draw_idle()

    @staticmethod
    def ax_drag_pan(self, button, key: str, x: float, y: float) -> None:
        """
        Handle mouse events during a pan operation.

        Notes
        -----
        This is intended to be overridden by new projection types.
        """
        points = self._get_pan_points(button, key, x, y)
        if points is not None:
            # Max and min needs to be defined at correct position for this to
            # work with inverted scaling
            ylim = points[:, 1]
            xlim = points[:, 0]
            self.set_xlim(min(xlim), max(xlim))
            self.set_ylim(min(ylim), max(ylim))

    # Overwritten function - do not change name
    def draw_rubberband(self, _event, x0, y0, x1, y1) -> None:
        self.canvas._rubberband_rect = [
            int(val) for val in
            (x0, self.canvas.figure.bbox.height - y0, x1 - x0, y0 - y1)
        ]
        self.canvas.queue_draw()

    # Overwritten function - do not change name
    def remove_rubberband(self) -> None:
        self.canvas._rubberband_rect = None
        self.canvas.queue_draw()

    # Overwritten function - do not change name
    def push_current(self, *_args) -> None:
        """Use custom functionality for the view clipboard."""
        self.canvas.highlight.load(self.canvas)
        for direction in ("bottom", "left", "top", "right"):
            self.canvas.notify(f"min-{direction}")
            self.canvas.notify(f"max-{direction}")
        self.canvas.emit("view_changed")

    # Overwritten function - do not change name
    def save_figure(self) -> None:
        pass


class _Highlight(SpanSelector):

    def __init__(self, canvas: Canvas):
        super().__init__(
            canvas.axes[3],
            lambda _x,
            _y: self.apply(canvas),
            "horizontal",
            useblit=True,
            props={
                "facecolor": canvas.rubberband_fill_color,
                "edgecolor": canvas.rubberband_edge_color,
                "linewidth": 1,
            },
            handle_props={"linewidth": 0},
            interactive=True,
            drag_from_anywhere=True,
        )
        self.load(canvas)

    def load(self, canvas: Canvas) -> None:
        xmin, xmax = canvas.axes[1].get_xlim()
        scale = scales.Scale(canvas.props.top_scale).value
        self.extents = (
            utilities.get_value_at_fraction(
                canvas.get_min_selected(),
                xmin,
                xmax,
                scale,
            ),
            utilities.get_value_at_fraction(
                canvas.get_max_selected(),
                xmin,
                xmax,
                scale,
            ),
        )

    def apply(self, canvas: Canvas) -> None:
        xmin, xmax = canvas.axes[1].get_xlim()
        extents = self.extents
        extents = max(xmin, extents[0]), min(xmax, extents[1])
        self.extents = extents

        for prefix, value in zip(["min_", "max_"], extents):
            canvas.set_property(
                prefix + "selected",
                utilities.get_fraction_at_value(
                    value,
                    xmin,
                    xmax,
                    canvas.props.top_scale,
                ),
            )
