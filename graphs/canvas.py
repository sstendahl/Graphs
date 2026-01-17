# SPDX-License-Identifier: GPL-3.0-or-later
"""
Custom canvas implementation.

Acts as an interface between matplotlib and GObject and contains a custom
implementation of a `SpanSelector` as well as a dummy toolbar used for
interactive navigation in conjunction with graphs-specific structures.
"""
import math
from typing import Tuple

from gi.repository import Adw, Gdk, Gio, Graphs, Gtk

from graphs import scales, utilities
from graphs.figure import Figure

from matplotlib import RcParams, backend_tools as tools
from matplotlib.backend_bases import (
    FigureCanvasBase,
    MouseEvent,
    NavigationToolbar2,
)
from matplotlib.backends.backend_gtk4cairo import FigureCanvas
from matplotlib.widgets import SpanSelector

_SCROLL_SCALE = 1.08


class Canvas(Graphs.Canvas, FigureCanvas):
    """Custom Canvas."""

    __gtype_name__ = "GraphsPythonCanvas"

    def __init__(
        self,
        style_params: Tuple[RcParams, dict],
        items: Gio.ListModel,
        interactive: bool = True,
    ):
        """
        Create the canvas.

        Create figure, axes and define rubberband_colors based on the current
        style context. Bind `items` to `data.items` and all figure settings
        attributes to their respective values.
        """
        Graphs.Canvas.__init__(
            self,
            hexpand=True,
            vexpand=True,
        )
        self._idle_draw_id = 0
        self.set_draw_func(self._draw_func)
        self.connect("resize", self.resize_event)
        self.connect("notify::scale-factor", self._update_device_pixel_ratio)
        FigureCanvasBase.__init__(
            self, figure=Figure(style_params, items, self))
        self._rubberband_rect = None

        # Handle stuff only used if the canvas is interactive
        if interactive:
            self._setup_interactive()

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
        for ax in self.figure.axes:
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
        """
        Handle scroll event.

        Updates only axes with independent coordinate systems to prevent uneven
        scaling:
        - X-limits: _axis and _top_left_axis (independent x ax.)
        - Y-limits: _axis, _right_axis, and _top_right_axis (independent y ax.)
        """
        if self._ctrl_held:
            self.zoom(1 / _SCROLL_SCALE if dy > 0 else _SCROLL_SCALE)
        else:
            if self._shift_held:
                dx, dy = dy, dx
            if controller.get_unit() == Gdk.ScrollUnit.WHEEL:
                dx *= 10
                dy *= 10

            for ax in [self.figure.axis, self.figure.top_left_axis]:
                xmin, xmax = ax.get_xlim()
                scale = scales.Scale.from_string(ax.get_xscale())
                xmin, xmax = self._calculate_pan_values(xmin, xmax, scale, dx)
                ax.set_xlim(xmin, xmax)

            for ax in [
                self.figure.axis,
                self.figure.right_axis,
                self.figure.top_right_axis,
            ]:
                ymin, ymax = ax.get_ylim()
                scale = scales.Scale.from_string(ax.get_yscale())
                ymin, ymax = self._calculate_pan_values(ymin, ymax, scale, -dy)
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
        scale = 1 + 0.015 * (scale - 1)
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
            xlim = self.figure.top_right_axis.get_xlim()
            ylim = self.figure.top_right_axis.get_ylim()
            self._xfrac = utilities.get_fraction_at_value(
                event.xdata,
                xlim[0],
                xlim[1],
                self.figure.props.top_scale,
            )
            self._yfrac = utilities.get_fraction_at_value(
                event.ydata,
                ylim[0],
                ylim[1],
                self.figure.props.right_scale,
            )
        else:
            self._xfrac, self._yfrac = None, None

    def zoom(self, scaling: float = 1.25, respect_mouse: bool = True) -> None:
        """
        Zoom with given scaling.

        Update all axes' limits in respect to the current mouse position,
        updates only axes with independent coordinate systems to prevent uneven
        scaling:
        - X-limits: _axis and _top_left_axis (independent x-ax.)
        - Y-limits: _axis, _right_axis, and _top_right_axis (independent y-ax.)
        """
        if not respect_mouse:
            self._xfrac, self._yfrac = 0.5, 0.5
        if self._xfrac is None or self._yfrac is None:
            return

        for ax in [self.figure.axis, self.figure.top_left_axis]:
            ax.set_xlim(
                self._calculate_zoomed_values(
                    self._xfrac,
                    scales.Scale.from_string(ax.get_xscale()),
                    ax.get_xlim(),
                    scaling,
                ),
            )
        for ax in [
            self.figure.axis,
            self.figure.right_axis,
            self.figure.top_right_axis,
        ]:
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
        current_min: float,
        current_max: float,
        scale: scales.Scale,
        panspeed: float,
    ) -> tuple[float, float]:
        """Calculate axis values required for panning."""
        pan_scale = 0.003

        value1 = utilities.get_value_at_fraction(
            panspeed * pan_scale,
            current_min,
            current_max,
            scale.value,
        )
        value2 = utilities.get_value_at_fraction(
            1 + panspeed * pan_scale,
            current_min,
            current_max,
            scale.value,
        )

        if scale == scales.Scale.INVERSE:
            value1, value2 = value2, value1

        return value1, value2

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

    def _on_pick(self, event) -> None:
        """Emit edit-request signal for picked label, tick or title."""
        artist = event.artist

        if not hasattr(artist, "id"):
            artist.id = self._determine_figure_setting(artist)

        self.emit("edit_request", artist.id)

    def _determine_figure_setting(self, artist) -> str:
        """
        Determine the figure settings to be used on the tick after pick event.

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

        min_val = self.figure.get_property(f"min_{side}")
        max_val = self.figure.get_property(f"max_{side}")
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

    def _on_mode_change(self, *_args) -> None:
        highlight_enabled = self.props.mode == 2
        self.highlight.set_active(highlight_enabled)
        self.highlight.set_visible(highlight_enabled)
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
            self.canvas.figure.notify(f"min-{direction}")
            self.canvas.figure.notify(f"max-{direction}")
        self.canvas.emit("view_changed")

    # Overwritten function - do not change name
    def save_figure(self) -> None:
        pass


class _Highlight(SpanSelector):

    def __init__(self, canvas: Canvas):
        super().__init__(
            canvas.figure.top_right_axis,
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
        canvas.figure.top_right_axis.callbacks.connect(
            "xlim_changed",
            lambda _x: self.load(canvas),
        )
        self.load(canvas)

    def load(self, canvas: Canvas) -> None:
        xmin, xmax = canvas.figure.top_left_axis.get_xlim()
        scale = scales.Scale(canvas.figure.props.top_scale).value
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
        xmin, xmax = canvas.figure.top_left_axis.get_xlim()
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
                    canvas.figure.props.top_scale,
                ),
            )
