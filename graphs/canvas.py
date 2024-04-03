# SPDX-License-Identifier: GPL-3.0-or-later
"""
Custom canvas implementation.

Acts as an interface between matplotlib and GObject and contains a custom
implementation of a `SpanSelector` as well as a dummy toolbar used for
interactive navigation in conjunction with graphs-specific structures.

    Classes:
        Canvas
"""
from contextlib import nullcontext

from gi.repository import GObject, Gdk, Graphs, Gtk

from graphs import artist, misc, scales, utilities

from matplotlib import backend_tools as tools, pyplot
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends.backend_gtk4cairo import FigureCanvas
from matplotlib.widgets import SpanSelector

_SCROLL_SCALE = 1.06


class Canvas(FigureCanvas, Graphs.CanvasInterface):
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
        edit-request
        view-changed

    Functions:
        update_legend
    """

    __gtype_name__ = "GraphsCanvas"
    __gsignals__ = {
        "edit-request": (GObject.SIGNAL_RUN_FIRST, None, (str, )),
        "view-changed": (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    hide_unselected = GObject.Property(type=bool, default=False)
    items = GObject.Property(type=object)
    mode = GObject.Property(type=int, default=0)

    min_selected = GObject.Property(type=float, default=0)
    max_selected = GObject.Property(type=float, default=0)

    def __init__(
        self,
        style_params: dict,
        interactive: bool = True,
        key_controller: Gtk.EventControllerKey = None,
    ):
        """
        Create the canvas.

        Create figure, axes and define rubberband_colors based on the current
        style context. Bind `items` to `data.items` and all figure settings
        attributes to their respective values.
        """
        self._style_params = style_params
        pyplot.rcParams.update(self._style_params)  # apply style_params
        GObject.Object.__init__(self, can_focus=False, items=[])
        super().__init__()
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

        # Handle stuff only used if the canvas is interactive
        if interactive:
            self.mpl_connect("pick_event", self._on_pick)

            def rgba_to_tuple(rgba):
                return (rgba.red, rgba.green, rgba.blue, rgba.alpha)

            rgba = self.get_style_context().lookup_color("accent_color")[1]
            self.rubberband_edge_color = rgba_to_tuple(rgba)
            rgba.alpha = 0.3
            self.rubberband_fill_color = rgba_to_tuple(rgba)

            self.highlight = _Highlight(self)
            # Reference is created by the toolbar itself
            _DummyToolbar(self)
            self.mpl_connect("scroll_event", self._on_scroll_event)
            self.mpl_connect("motion_notify_event", self._set_mouse_fraction)
            self._xfrac, self._yfrac = None, None
            zoom_gesture = Gtk.GestureZoom.new()
            zoom_gesture.connect("scale-changed", self._on_zoom_gesture)
            zoom_gesture.connect(
                "end",
                self.figure.canvas.toolbar.push_current,
            )
            scroll_gesture = Gtk.EventControllerScroll.new(
                Gtk.EventControllerScrollFlags.BOTH_AXES,
            )
            scroll_gesture.connect("scroll", self._on_pan_gesture)
            scroll_gesture.connect(
                "scroll-end",
                self.figure.canvas.toolbar.push_current,
            )
            self._ctrl_held = False
            self._shift_held = False
            self.add_controller(zoom_gesture)
            self.add_controller(scroll_gesture)

            if key_controller is not None:
                key_controller.connect("key-pressed", self._on_key_press_event)
                key_controller.connect(
                    "key-released",
                    self._on_key_release_event,
                )

            for item in ("min", "max"):
                self.connect(
                    f"notify::{item}-selected",
                    lambda _a,
                    _b: self.highlight.load(self),
                )

        self.connect("notify::hide-unselected", self._redraw)
        self.connect("notify::items", self._redraw)

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

    def _on_zoom_gesture(self, _gesture, scale: float) -> None:
        scale = 1 + 0.02 * (scale - 1)
        if scale > 5 or scale < 0.2:
            # Don't scale if ridiculous values are registered
            return
        self.zoom(scale)

    def _on_pan_gesture(self, event_controller, x: float, y: float) -> None:
        """
        Handle pan gesture.

        Determines what to do when a panning gesture is detected, pans the
        canvas in the gesture direction.
        """
        if self._ctrl_held is False:
            if self._shift_held:
                x, y = y, x
            if event_controller.get_unit() == Gdk.ScrollUnit.WHEEL:
                x *= 10
                y *= 10
            for ax in self.axes:
                xmin, xmax, ymin, ymax = \
                    self._calculate_pan_values(ax, x, y)
                ax.set_xlim(xmin, xmax)
                ax.set_ylim(ymin, ymax)
            self.queue_draw()

    def _on_scroll_event(self, event) -> None:
        """
        Handle mouse scrolling.

        Determines what to do when a scroll signal is detected, scrolls the
        canvas if ctrl is selected.
        """
        if self._ctrl_held is True:
            self.zoom(
                1 / _SCROLL_SCALE if event.button == "up" else _SCROLL_SCALE,
            )

    def _on_key_press_event(
        self,
        _controller,
        keyval: int,
        _keycode,
        _state,
    ) -> None:
        """
        Handle keyboard inputs.

        Checks if control is pressed, needed to allow ctrl+scroll behaviour
        as the key press event from matplotlib is not working properly atm.
        """
        if keyval == 65507 or keyval == 65508:  # Control_L or Control_R
            self._ctrl_held = True
        elif keyval == 65505 or keyval == 65506:  # Left or right Shift
            self._shift_held = True
        else:  # Prevent keys from being true with key combos
            self._ctrl_held = False

    def _on_key_release_event(
        self,
        _controller,
        _keyval,
        _keycode,
        _state,
    ) -> None:
        """
        Handle keyboard inputs.

        Checks if control is released, needed to allow ctrl+scroll behaviour
        as the key press event from matplotlib is not working properly atm.
        """
        self._ctrl_held = False
        self._shift_held = False

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
                    scales.to_int(ax.get_xscale()),
                    ax.get_xlim(),
                    scaling,
                ),
            )
            ax.set_ylim(
                self._calculate_zoomed_values(
                    self._yfrac,
                    scales.to_int(ax.get_yscale()),
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
        x_scale = scales.to_int(ax.get_xscale())
        y_scale = scales.to_int(ax.get_yscale())
        pan_scale = 0.002
        xvalue1 = utilities.get_value_at_fraction(
            x_panspeed * pan_scale,
            xmin,
            xmax,
            x_scale,
        )
        xvalue2 = utilities.get_value_at_fraction(
            1 + x_panspeed * pan_scale,
            xmin,
            xmax,
            x_scale,
        )
        yvalue1 = utilities.get_value_at_fraction(
            -y_panspeed * pan_scale,
            ymin,
            ymax,
            y_scale,
        )
        yvalue2 = utilities.get_value_at_fraction(
            1 - y_panspeed * pan_scale,
            ymin,
            ymax,
            y_scale,
        )
        if x_scale == 4:
            xvalue1, xvalue2 = xvalue2, xvalue1
        if y_scale == 4:
            yvalue1, yvalue2 = yvalue2, yvalue1
        return xvalue1, xvalue2, yvalue1, yvalue2

    @staticmethod
    def _calculate_zoomed_values(
        fraction: float,
        scale: float,
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
            scale,
        )
        value2 = utilities.get_value_at_fraction(
            fraction + (1 - fraction) / zoom_factor,
            min_,
            max_,
            scale,
        )
        if scale == 4:
            value1, value2 = value2, value1
        return value1, value2

    def on_draw_event(self, _widget, ctx) -> None:
        """
        Overwrite super function.

        Fixes a UI scaling bug, see
        https://gitlab.gnome.org/World/Graphs/-/issues/259
        """
        with (
            self.toolbar._wait_cursor_for_draw_cm()
            if self.toolbar else nullcontext()
        ):
            self._renderer.set_context(ctx)
            scale = self.device_pixel_ratio
            # Scale physical drawing to logical size.
            ctx.scale(1 / scale, 1 / scale)
            allocation = self.get_allocation()
            Gtk.render_background(
                self.get_style_context(),
                ctx,
                allocation.x,
                allocation.y,
                allocation.width,
                allocation.height,
            )
            self._renderer.width = allocation.width * scale
            self._renderer.height = allocation.height * scale
            self._renderer.dpi = self.figure.dpi
            self.figure.draw(self._renderer)

    def _redraw(self, *_args) -> None:
        # bottom, top, left, right
        used_axes = [False, False, False, False]
        visible_axes = [False, False, False, False]
        if self.props.hide_unselected:
            drawable_items = []
            for item in self.props.items:
                if hasattr(item, "handler"):
                    item.disconnect(item.handler)
                item.handler = item.connect("notify::selected", self._redraw)
                if item.get_selected():
                    drawable_items.append(item)
        else:
            drawable_items = self.props.items
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
        """Emit edit-request signal for picked label/title."""
        self.emit("edit-request", event.artist.id)

    # Overwritten function - do not change name
    def _post_draw(self, _widget, context) -> None:
        """Allow custom rendering extensions."""
        if self._rubberband_rect is not None:
            self._draw_rubberband(context)

    def _draw_rubberband(self, context) -> None:
        """
        Implement custom rubberband.

        Draw a rubberband matching libadwaitas style, where `_rubberband_rect`
        is set.
        """
        line_width = 1
        if not self._context_is_scaled:
            x_0, y_0, width, height = (
                dim / self.device_pixel_ratio for dim in self._rubberband_rect
            )
        else:
            x_0, y_0, width, height = self._rubberband_rect
            line_width *= self.device_pixel_ratio

        context.set_antialias(1)
        context.set_line_width(line_width)
        context.rectangle(x_0, y_0, width, height)
        color = self.rubberband_fill_color
        context.set_source_rgba(color[0], color[1], color[2], color[3])
        context.fill()
        context.rectangle(x_0, y_0, width, height)
        color = self.rubberband_edge_color
        context.set_source_rgba(color[0], color[1], color[2], color[3])
        context.stroke()

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
        return scales.to_int(self._axis.get_xscale())

    @bottom_scale.setter
    def bottom_scale(self, scale: int) -> None:
        scale = scales.to_string(scale)
        for axis in (self._axis, self._right_axis):
            axis.set_xscale(scale)
            axis.set_xlim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def left_scale(self) -> int:
        """Scale of the left axis."""
        return scales.to_int(self._axis.get_yscale())

    @left_scale.setter
    def left_scale(self, scale: int) -> None:
        scale = scales.to_string(scale)
        for axis in (self._axis, self._top_left_axis):
            axis.set_yscale(scale)
            axis.set_ylim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def top_scale(self) -> int:
        """Scale of the top axis."""
        return scales.to_int(self._top_left_axis.get_xscale())

    @top_scale.setter
    def top_scale(self, scale: int) -> None:
        scale = scales.to_string(scale)
        for axis in (self._top_right_axis, self._top_left_axis):
            axis.set_xscale(scale)
            axis.set_xlim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def right_scale(self) -> int:
        """Scale of the right axis."""
        return scales.to_int(self._right_axis.get_yscale())

    @right_scale.setter
    def right_scale(self, scale: int) -> None:
        scale = scales.to_string(scale)
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

    @GObject.Property(type=bool, default=False)
    def highlight_enabled(self) -> bool:
        """Whether or not the highlight is enabled."""
        return hasattr(self, "highlight") and self.highlight.get_active()

    @highlight_enabled.setter
    def highlight_enabled(self, enabled: bool) -> None:
        if hasattr(self, "highlight"):
            self.highlight.set_active(enabled)
            self.highlight.set_visible(enabled)
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
        self.canvas.emit("view-changed")

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
        scale = canvas.props.top_scale
        self.extents = (
            utilities.get_value_at_fraction(
                canvas.min_selected,
                xmin,
                xmax,
                scale,
            ),
            utilities.get_value_at_fraction(
                canvas.max_selected,
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
