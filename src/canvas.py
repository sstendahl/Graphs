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

from gi.repository import Adw, GObject, Gtk

from graphs import artist, misc, utilities
from graphs.figure_settings import FigureSettingsWindow

from matplotlib import backend_tools as tools, pyplot
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends.backend_gtk4cairo import FigureCanvas
from matplotlib.widgets import SpanSelector


def _scale_to_string(scale: int) -> str:
    return "linear" if scale == 0 else "log"


def _scale_to_int(scale: str) -> int:
    return 0 if scale == "linear" else 1


class Canvas(FigureCanvas):
    """
    Custom Canvas.

    Implements properties analouge to `FigureSettings`. Automatically connects
    to `FigureSettings` and `Data.items` during init.

    Properties:
        application

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

    Functions:
        get_application
        update_legend
    """

    __gtype_name__ = "Canvas"

    application = GObject.Property(type=Adw.Application)

    min_selected = GObject.Property(type=float, default=0)
    max_selected = GObject.Property(type=float, default=0)

    def __init__(self, application):
        """
        Create the canvas.

        Create figure, axes and define rubberband_colors based on the current
        style context. Bind `items` to `data.items` and all figure settings
        attributes to their respective values.
        """
        GObject.Object.__init__(self, application=application)
        super().__init__()
        self.set_can_focus(False)
        self.figure.set_tight_layout(True)
        self.mpl_connect("pick_event", self._on_pick)
        self.axis = self.figure.add_subplot(111)
        self.right_axis = self.axis.twinx()
        self.top_left_axis = self.axis.twiny()
        self.top_right_axis = self.top_left_axis.twinx()
        self.axes = [
            self.axis, self.top_left_axis,
            self.right_axis, self.top_right_axis,
        ]
        color_rgba = self.get_style_context().lookup_color("accent_color")[1]
        self.rubberband_edge_color = utilities.rgba_to_tuple(color_rgba, True)
        color_rgba.alpha = 0.3
        self.rubberband_fill_color = utilities.rgba_to_tuple(color_rgba, True)
        # Reference is created by the toolbar itself
        _DummyToolbar(self)
        self.highlight = _Highlight(self)
        self._legend = True
        self._legend_position = misc.LEGEND_POSITIONS[0]
        self._handles = []

        for prop in dir(self.get_application().get_figure_settings().props):
            if prop not in ["use_custom_style", "custom_style"]:
                self.get_application().get_figure_settings().bind_property(
                    prop, self, prop, 1 | 2,
                )
        self.get_application().get_data().bind_property(
            "items", self, "items", 2,
        )

    def get_application(self):
        """Get application property."""
        return self.props.application

    def on_draw_event(self, _widget, ctx):
        """
        Overwrite super function.

        Fixes a UI scaling bug, see
        https://github.com/Sjoerd1993/Graphs/issues/259
        """
        with (self.toolbar._wait_cursor_for_draw_cm() if self.toolbar
              else nullcontext()):
            self._renderer.set_context(ctx)
            scale = self.device_pixel_ratio
            # Scale physical drawing to logical size.
            ctx.scale(1 / scale, 1 / scale)
            allocation = self.get_allocation()
            Gtk.render_background(
                self.get_style_context(), ctx,
                allocation.x, allocation.y,
                allocation.width, allocation.height)
            self._renderer.width = allocation.width * scale
            self._renderer.height = allocation.height * scale
            self._renderer.dpi = self.figure.dpi
            self.figure.draw(self._renderer)

    @GObject.Property(flags=2)
    def items(self):
        """ignored, property is write-only."""

    @items.setter
    def items(self, items: list):
        """
        Setter for items property.

        Automatically hide unused axes and refresh legend.
        """
        hide_unselected = self.get_application().get_settings(
            "general").get_boolean("hide-unselected")
        drawable_items = []
        # bottom, top, left, right
        used_axes = [False, False, False, False]
        for item in items:
            if item.selected and not hide_unselected:
                drawable_items.append(item)
                used_axes[item.xposition] = True
                used_axes[2 + item.yposition] = True
        axes_directions = [
            ["bottom", "left"],   # axis
            ["top", "left"],      # top_left_axis
            ["bottom", "right"],  # right_axis
            ["top", "right"],     # top_right_axis
        ]
        if not any(used_axes):
            used_axes = [True, False, True, False]

        ticks = "both" if pyplot.rcParams["xtick.minor.visible"] else "major"
        for count, directions in enumerate(axes_directions):
            axis = self.axes[count]
            axis.get_xaxis().set_visible(False)
            axis.get_yaxis().set_visible(False)
            # Set tick where requested, as long as that axis is not occupied
            axis.tick_params(which=ticks, **{
                key: pyplot.rcParams[f"{'x' if i < 2 else 'y'}tick.{key}"]
                and (key in directions or not used_axes[i])
                for i, key in enumerate(["bottom", "top", "left", "right"])
            })
            for handle in axis.lines + axis.texts:
                handle.remove()
        self.axis.get_xaxis().set_visible(used_axes[0])
        self.top_left_axis.get_xaxis().set_visible(used_axes[1])
        self.axis.get_yaxis().set_visible(used_axes[2])
        self.right_axis.get_yaxis().set_visible(used_axes[3])

        self._handles = [
            artist.new_for_item(self, item)
            for item in reversed(drawable_items)
        ]
        self.update_legend()

    def _on_pick(self, event):
        """Invoke FigureSettingsWindow for picked label/title."""
        FigureSettingsWindow(self.get_application(), event.artist.id)

    # Overwritten function - do not change name
    def _post_draw(self, _widget, context):
        """Allow custom rendering extensions."""
        if self._rubberband_rect is not None:
            self._draw_rubberband(context)

    def _draw_rubberband(self, context):
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

    def update_legend(self):
        """Update the legend or hide if not used."""
        if self._legend and self._handles:
            handles = [
                handle.get_artist() for handle in self._handles
                if handle.legend
            ]
            if handles:
                self.top_right_axis.legend(
                    handles=handles, loc=self._legend_position,
                    frameon=True, reverse=True,
                )
                self.queue_draw()
                return
        if self.top_right_axis.get_legend() is not None:
            self.top_right_axis.get_legend().remove()
        self.queue_draw()

    @GObject.Property(type=bool, default=True)
    def legend(self) -> bool:
        """Whether or not, the legend is visible."""
        return self._legend

    @legend.setter
    def legend(self, legend: bool):
        self._legend = legend
        self.update_legend()

    @GObject.Property(type=int, default=0)
    def legend_position(self) -> int:
        """Legend Position (see `misc.LEGEND_POSITIONS`)."""
        return misc.LEGEND_POSITIONS.index(self._legend_position)

    @legend_position.setter
    def legend_position(self, legend_position: int):
        self._legend_position = misc.LEGEND_POSITIONS[legend_position]
        self.update_legend()

    @GObject.Property(type=str)
    def title(self) -> str:
        """Figure title."""
        return self.axis.get_title()

    @title.setter
    def title(self, title: str):
        self.axis.set_title(title, picker=True).id = "title"
        self.queue_draw()

    @GObject.Property(type=str)
    def bottom_label(self) -> str:
        """Label of the bottom axis."""
        return self.axis.get_xlabel()

    @bottom_label.setter
    def bottom_label(self, label: str):
        self.axis.set_xlabel(label, picker=True).id = "bottom_label"
        self.queue_draw()

    @GObject.Property(type=str)
    def left_label(self) -> str:
        """Label of the left axis."""
        return self.axis.get_ylabel()

    @left_label.setter
    def left_label(self, label: str):
        self.axis.set_ylabel(label, picker=True).id = "left_label"
        self.queue_draw()

    @GObject.Property(type=str)
    def top_label(self) -> str:
        """Label of the top axis."""
        return self.top_left_axis.get_xlabel()

    @top_label.setter
    def top_label(self, label: str):
        self.top_left_axis.set_xlabel(label, picker=True).id = "top_label"
        self.queue_draw()

    @GObject.Property(type=str)
    def right_label(self) -> str:
        """Label of the right axis."""
        return self.right_axis.get_ylabel()

    @right_label.setter
    def right_label(self, label: str):
        self.right_axis.set_ylabel(label, picker=True).id = "right_label"
        self.queue_draw()

    @GObject.Property(type=int)
    def bottom_scale(self) -> int:
        """Scale of the bottom axis."""
        return _scale_to_int(self.axis.get_xscale())

    @bottom_scale.setter
    def bottom_scale(self, scale: int):
        scale = _scale_to_string(scale)
        for axis in [self.axis, self.right_axis]:
            axis.set_xscale(scale)
            axis.set_xlim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def left_scale(self) -> int:
        """Scale of the left axis."""
        return _scale_to_int(self.axis.get_yscale())

    @left_scale.setter
    def left_scale(self, scale: int):
        scale = _scale_to_string(scale)
        for axis in [self.axis, self.top_left_axis]:
            axis.set_yscale(scale)
            axis.set_ylim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def top_scale(self) -> int:
        """Scale of the top axis."""
        return _scale_to_int(self.top_left_axis.get_xscale())

    @top_scale.setter
    def top_scale(self, scale: int):
        scale = _scale_to_string(scale)
        for axis in [self.top_right_axis, self.top_left_axis]:
            axis.set_xscale(scale)
            axis.set_xlim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def right_scale(self) -> int:
        """Scale of the right axis."""
        return _scale_to_int(self.right_axis.get_yscale())

    @right_scale.setter
    def right_scale(self, scale: int):
        scale = _scale_to_string(scale)
        for axis in [self.top_right_axis, self.right_axis]:
            axis.set_yscale(scale)
            axis.set_ylim(None, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_bottom(self) -> float:
        """Lower limit for the bottom axis."""
        return self.axis.get_xlim()[0]

    @min_bottom.setter
    def min_bottom(self, value: float):
        for axis in [self.axis, self.right_axis]:
            axis.set_xlim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_bottom(self) -> float:
        """Upper limit for the bottom axis."""
        return self.axis.get_xlim()[1]

    @max_bottom.setter
    def max_bottom(self, value: float):
        for axis in [self.axis, self.right_axis]:
            axis.set_xlim(None, value)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_left(self) -> float:
        """Lower limit for the left axis."""
        return self.axis.get_ylim()[0]

    @min_left.setter
    def min_left(self, value: float):
        for axis in [self.axis, self.top_left_axis]:
            axis.set_ylim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_left(self) -> float:
        """Upper limit for the left axis."""
        return self.axis.get_ylim()[1]

    @max_left.setter
    def max_left(self, value: float):
        for axis in [self.axis, self.top_left_axis]:
            axis.set_ylim(None, value)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_top(self) -> float:
        """Lower limit for the top axis."""
        return self.top_left_axis.get_xlim()[0]

    @min_top.setter
    def min_top(self, value: float):
        for axis in [self.top_left_axis, self.top_right_axis]:
            axis.set_xlim(value, None)
        self.highlight.load(self)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_top(self) -> float:
        """Upper limit for the top axis."""
        return self.top_left_axis.get_xlim()[1]

    @max_top.setter
    def max_top(self, value: float):
        for axis in [self.top_left_axis, self.top_right_axis]:
            axis.set_xlim(None, value)
        self.highlight.load(self)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_right(self) -> float:
        """Lower limit for the right axis."""
        return self.right_axis.get_ylim()[0]

    @min_right.setter
    def min_right(self, value: float):
        for axis in [self.right_axis, self.top_right_axis]:
            axis.set_ylim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_right(self) -> float:
        """Upper limit for the right axis."""
        return self.right_axis.get_ylim()[1]

    @max_right.setter
    def max_right(self, value: float):
        for axis in [self.right_axis, self.top_right_axis]:
            axis.set_ylim(None, value)
        self.queue_draw()

    @GObject.Property(type=bool, default=False)
    def highlight_enabled(self) -> bool:
        """Whether or not the highlight is enabled."""
        return self.highlight.get_active()

    @highlight_enabled.setter
    def highlight_enabled(self, enabled: bool):
        self.highlight.set_active(enabled)
        self.highlight.set_visible(enabled)
        self.queue_draw()


class _DummyToolbar(NavigationToolbar2):
    """Custom Toolbar implementation."""

    # Overwritten function - do not change name
    def _zoom_pan_handler(self, event):
        if event.button != 1:
            return
        mode = self.canvas.get_application().get_mode()
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
    def _update_cursor(self, event):
        mode = self.canvas.get_application().get_mode()
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
    def draw_rubberband(self, _event, x0, y0, x1, y1):
        self.canvas._rubberband_rect = [
            int(val) for val
            in (x0, self.canvas.figure.bbox.height - y0, x1 - x0, y0 - y1)
        ]
        self.canvas.queue_draw()

    # Overwritten function - do not change name
    def remove_rubberband(self):
        self.canvas._rubberband_rect = None
        self.canvas.queue_draw()

    # Overwritten function - do not change name
    def push_current(self):
        """Use custom functionality for the view clipboard."""
        self.canvas.highlight.load(self.canvas)
        for direction in ["bottom", "left", "top", "right"]:
            self.canvas.notify(f"min-{direction}")
            self.canvas.notify(f"max-{direction}")
        self.canvas.application.get_view_clipboard().add()

    # Overwritten function - do not change name
    def save_figure(self):
        pass


class _Highlight(SpanSelector):
    def __init__(self, canvas):
        super().__init__(
            canvas.top_right_axis,
            lambda _x, _y: self.apply(canvas),
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

    def load(self, canvas):
        xmin, xmax = canvas.top_right_axis.get_xlim()
        scale = _scale_to_int(canvas.top_left_axis.get_xscale())
        self.extents = (
            utilities.get_value_at_fraction(
                canvas.min_selected, xmin, xmax, scale,
            ),
            utilities.get_value_at_fraction(
                canvas.max_selected, xmin, xmax, scale,
            ),
        )

    def apply(self, canvas):
        xmin, xmax = canvas.top_right_axis.get_xlim()
        extents = self.extents
        extents = max(xmin, extents[0]), min(xmax, extents[1])
        self.extents = extents

        scale = _scale_to_int(canvas.top_left_axis.get_xscale())
        for i, prefix in enumerate(["min_", "max_"]):
            canvas.set_property(
                prefix + "selected",
                utilities.get_fraction_at_value(extents[i], xmin, xmax, scale),
            )
