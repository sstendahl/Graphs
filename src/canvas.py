# SPDX-License-Identifier: GPL-3.0-or-later
import time
from contextlib import nullcontext

from gi.repository import Adw, GObject, Gtk

from graphs import artist, utilities
from graphs.rename import RenameWindow

from matplotlib import backend_tools as tools, pyplot
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends.backend_gtk4cairo import FigureCanvas
from matplotlib.widgets import SpanSelector

LEGEND_POSITIONS = [
    "best", "upper right", "upper left", "lower left", "lower right",
    "center left", "center right", "lower center", "upper center", "center",
]


def _scale_to_string(scale):
    return "linear" if scale == 0 else "log"


def _scale_to_int(scale):
    return 0 if scale == "linear" else 1


class Canvas(FigureCanvas):
    __gtype_name__ = "Canvas"

    application = GObject.Property(type=Adw.Application)
    one_click_trigger = GObject.Property(type=bool, default=False)
    time_first_click = GObject.Property(type=float, default=0)

    min_selected = GObject.Property(type=float, default=0)
    max_selected = GObject.Property(type=float, default=0)

    def __init__(self, application):
        GObject.Object.__init__(self, application=application)
        super().__init__()
        self.figure.set_tight_layout(True)
        self.mpl_connect("button_release_event", self)
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
        DummyToolbar(self)
        self.highlight = Highlight(self)
        self._legend = True
        self._legend_position = LEGEND_POSITIONS[0]
        self._handles = []

        for prop in dir(self.props.application.props.figure_settings.props):
            if prop not in ["use_custom_style", "custom_style"]:
                self.props.application.props.figure_settings.bind_property(
                    prop, self, prop, 1 | 2,
                )
        self.props.application.props.data.bind_property(
            "items", self, "items", 2,
        )

    # Temporarily overwritten function, see
    # https://github.com/Sjoerd1993/Graphs/issues/259
    def on_draw_event(self, _widget, ctx):
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
        pass

    @items.setter
    def items(self, items):
        hide_unselected = self.props.application.get_settings(
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

    # Overwritten function - do not change name
    def __call__(self, event):
        """
        The function is called when a user clicks on it.
        If two clicks are performed close to each other, it registers as a
        double click, and if these were on a specific item (e.g. the title) it
        triggers a dialog to edit this item.

        Unfortunately the GTK Doubleclick signal doesn't work with matplotlib
        hence this custom function.
        """
        double_click_interval = time.time() - self.time_first_click
        if (not self.one_click_trigger) or (double_click_interval > 0.5):
            self.one_click_trigger = True
            self.time_first_click = time.time()
            return
        self.one_click_trigger = False
        self.time_first_click = 0
        items = {self._title, self._top_label, self._bottom_label,
                 self._left_label, self._right_label}
        for item in items:
            if item.contains(event)[0]:
                RenameWindow(self.props.application, item)

    # Overwritten function - do not change name
    def _post_draw(self, _widget, context):
        if self._rubberband_rect is not None:
            self.draw_rubberband(context)

    def draw_rubberband(self, context):
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
        return self._legend

    @legend.setter
    def legend(self, legend: bool):
        self._legend = legend
        self.update_legend()

    @GObject.Property(type=int, default=0)
    def legend_position(self) -> int:
        return LEGEND_POSITIONS.index(self._legend_position)

    @legend_position.setter
    def legend_position(self, legend_position: int):
        self._legend_position = LEGEND_POSITIONS[legend_position]
        self.update_legend()

    @GObject.Property(type=str)
    def title(self):
        return self.axis.get_title()

    @title.setter
    def title(self, title: str):
        self._title = self.axis.set_title(title)
        self.queue_draw()

    @GObject.Property(type=str)
    def bottom_label(self):
        return self.axis.get_xlabel()

    @bottom_label.setter
    def bottom_label(self, label: str):
        self._bottom_label = self.axis.set_xlabel(label)
        self.queue_draw()

    @GObject.Property(type=str)
    def left_label(self):
        return self.axis.get_ylabel()

    @left_label.setter
    def left_label(self, label: str):
        self._left_label = self.axis.set_ylabel(label)
        self.queue_draw()

    @GObject.Property(type=str)
    def top_label(self):
        return self.top_left_axis.get_xlabel()

    @top_label.setter
    def top_label(self, label: str):
        self._top_label = self.top_left_axis.set_xlabel(label)
        self.queue_draw()

    @GObject.Property(type=str)
    def right_label(self):
        return self.right_axis.get_ylabel()

    @right_label.setter
    def right_label(self, label: str):
        self._right_label = self.right_axis.set_ylabel(label)
        self.queue_draw()

    @GObject.Property(type=int)
    def bottom_scale(self):
        return _scale_to_int(self.axis.get_xscale())

    @bottom_scale.setter
    def bottom_scale(self, scale: int):
        scale = _scale_to_string(scale)
        for axis in [self.axis, self.right_axis]:
            axis.set_xscale(scale)
            axis.set_xlim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def left_scale(self):
        return _scale_to_int(self.axis.get_yscale())

    @left_scale.setter
    def left_scale(self, scale: int):
        scale = _scale_to_string(scale)
        for axis in [self.axis, self.top_left_axis]:
            axis.set_yscale(scale)
            axis.set_ylim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def top_scale(self):
        return _scale_to_int(self.top_left_axis.get_xscale())

    @top_scale.setter
    def top_scale(self, scale: int):
        scale = _scale_to_string(scale)
        for axis in [self.top_right_axis, self.top_left_axis]:
            axis.set_xscale(scale)
            axis.set_xlim(None, None)
        self.queue_draw()

    @GObject.Property(type=int)
    def right_scale(self):
        return _scale_to_int(self.right_axis.get_yscale())

    @right_scale.setter
    def right_scale(self, scale: int):
        scale = _scale_to_string(scale)
        for axis in [self.top_right_axis, self.right_axis]:
            axis.set_yscale(scale)
            axis.set_ylim(None, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_bottom(self):
        return self.axis.get_xlim()[0]

    @min_bottom.setter
    def min_bottom(self, value: float):
        for axis in [self.axis, self.right_axis]:
            axis.set_xlim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_bottom(self):
        return self.axis.get_xlim()[1]

    @max_bottom.setter
    def max_bottom(self, value: float):
        for axis in [self.axis, self.right_axis]:
            axis.set_xlim(None, value)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_left(self):
        return self.axis.get_ylim()[0]

    @min_left.setter
    def min_left(self, value: float):
        for axis in [self.axis, self.top_left_axis]:
            axis.set_ylim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_left(self):
        return self.axis.get_ylim()[1]

    @max_left.setter
    def max_left(self, value: float):
        for axis in [self.axis, self.top_left_axis]:
            axis.set_ylim(None, value)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_top(self):
        return self.top_left_axis.get_xlim()[0]

    @min_top.setter
    def min_top(self, value: float):
        for axis in [self.top_left_axis, self.top_right_axis]:
            axis.set_xlim(value, None)
        self.highlight.load(self)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_top(self):
        return self.top_left_axis.get_xlim()[1]

    @max_top.setter
    def max_top(self, value: float):
        for axis in [self.top_left_axis, self.top_right_axis]:
            axis.set_xlim(None, value)
        self.highlight.load(self)
        self.queue_draw()

    @GObject.Property(type=float)
    def min_right(self):
        return self.right_axis.get_ylim()[0]

    @min_right.setter
    def min_right(self, value: float):
        for axis in [self.right_axis, self.top_right_axis]:
            axis.set_ylim(value, None)
        self.queue_draw()

    @GObject.Property(type=float)
    def max_right(self):
        return self.right_axis.get_ylim()[1]

    @max_right.setter
    def max_right(self, value: float):
        for axis in [self.right_axis, self.top_right_axis]:
            axis.set_ylim(None, value)
        self.queue_draw()

    @GObject.Property(type=bool, default=False)
    def highlight_enabled(self) -> bool:
        return self.highlight.get_active()

    @highlight_enabled.setter
    def highlight_enabled(self, enabled: bool):
        self.highlight.set_active(enabled)
        self.highlight.set_visible(enabled)
        self.queue_draw()


class DummyToolbar(NavigationToolbar2):
    # Overwritten function - do not change name
    def _zoom_pan_handler(self, event):
        if event.button != 1:
            return
        mode = self.canvas.props.application.props.mode
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
        mode = self.canvas.props.application.props.mode
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
        self.canvas.highlight.load(self.canvas)
        for direction in ["bottom", "left", "top", "right"]:
            self.canvas.notify(f"min-{direction}")
            self.canvas.notify(f"max-{direction}")
        self.canvas.application.props.view_clipboard.add()

    # Overwritten function - do not change name
    def save_figure(self):
        pass


class Highlight(SpanSelector):
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
        canvas.props.min_selected = utilities.get_fraction_at_value(
            extents[0], xmin, xmax, scale,
        )
        canvas.props.max_selected = utilities.get_fraction_at_value(
            extents[1], xmin, xmax, scale,
        )
