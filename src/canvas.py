# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import time
from contextlib import nullcontext
from gettext import gettext as _

from gi.repository import Gtk

from graphs import utilities
from graphs.item import Item, TextItem
from graphs.misc import InteractionMode
from graphs.rename import RenameWindow

from matplotlib import backend_tools as tools, pyplot
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends.backend_gtk4cairo import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector


class Canvas(FigureCanvas):
    """Create the graph widget"""
    def __init__(self, application):
        self.application = application
        self.figure = Figure()
        self.figure.set_tight_layout(True)
        self.one_click_trigger = False
        self.time_first_click = 0
        self.mpl_connect("button_release_event", self)
        self.axis = self.figure.add_subplot(111)
        self.right_axis = self.axis.twinx()
        self.top_left_axis = self.axis.twiny()
        self.top_right_axis = self.top_left_axis.twinx()
        self.set_axis_properties()
        self.set_ticks()
        color_rgba = utilities.lookup_color(self.application, "accent_color")
        self.rubberband_edge_color = utilities.rgba_to_tuple(color_rgba, True)
        color_rgba.alpha = 0.3
        self.rubberband_fill_color = utilities.rgba_to_tuple(color_rgba, True)
        super().__init__(self.figure)
        self.limits = {
            "min_bottom": self.application.plot_settings.min_bottom,
            "max_bottom": self.application.plot_settings.max_bottom,
            "min_top": self.application.plot_settings.min_top,
            "max_top": self.application.plot_settings.max_top,
            "min_left": self.application.plot_settings.min_left,
            "max_left": self.application.plot_settings.max_left,
            "min_right": self.application.plot_settings.min_right,
            "max_right": self.application.plot_settings.max_right,
        }
        self.legends = []
        for axis in [self.right_axis, self.top_left_axis,
                     self.top_right_axis]:
            axis.get_xaxis().set_visible(False)
            axis.get_yaxis().set_visible(False)
        DummyToolbar(self)
        self.highlight = Highlight(self)

    # Temporarily overwritten function, see
    # https://github.com/Sjoerd1993/Graphs/issues/259
    def on_draw_event(self, widget, ctx):
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

    def plot(self, item):
        x_axis = item.plot_x_position
        y_axis = item.plot_y_position
        if y_axis == "left":
            if x_axis == "bottom":
                axis = self.axis
            elif x_axis == "top":
                axis = self.top_left_axis
        elif y_axis == "right":
            if x_axis == "bottom":
                axis = self.right_axis
            elif x_axis == "top":
                axis = self.top_right_axis
        common_parameters = {
            "color": item.color,
            "alpha": item.alpha,
        }
        if isinstance(item, Item):
            linewidth = item.linewidth
            markersize = item.markersize
            if not item.selected:
                linewidth *= 0.35
                markersize *= 0.35
            axis.plot(
                item.xdata, item.ydata,
                **common_parameters,
                marker=item.markerstyle, linestyle=item.linestyle,
                linewidth=linewidth, markersize=markersize, label=item.name)
        elif isinstance(item, TextItem):
            axis.text(
                item.x_anchor, item.y_anchor, item.text,
                **common_parameters,
                clip_on=True, fontsize=item.size, rotation=item.rotation)

    def apply_limits(self):
        plot_settings = self.application.plot_settings
        plot_settings.min_bottom = min(self.axis.get_xlim())
        plot_settings.max_bottom = max(self.axis.get_xlim())
        plot_settings.min_top = min(self.top_left_axis.get_xlim())
        plot_settings.max_top = max(self.top_left_axis.get_xlim())
        plot_settings.min_left = min(self.axis.get_ylim())
        plot_settings.max_left = max(self.axis.get_ylim())
        plot_settings.min_right = min(self.right_axis.get_ylim())
        plot_settings.max_right = max(self.right_axis.get_ylim())

    @property
    def limits(self):
        return {
            "min_bottom": min(self.axis.get_xlim()),
            "max_bottom": max(self.axis.get_xlim()),
            "min_top": min(self.top_left_axis.get_xlim()),
            "max_top": max(self.top_left_axis.get_xlim()),
            "min_left": min(self.axis.get_ylim()),
            "max_left": max(self.axis.get_ylim()),
            "min_right": min(self.right_axis.get_ylim()),
            "max_right": max(self.right_axis.get_ylim()),
        }

    @limits.setter
    def limits(self, value):
        try:
            for axis in [self.axis, self.right_axis]:
                axis.set_xlim(value["min_bottom"], value["max_bottom"])
            for axis in [self.top_left_axis, self.top_right_axis]:
                axis.set_xlim(value["min_top"], value["max_top"])
            for axis in [self.axis, self.top_left_axis]:
                axis.set_ylim(value["min_left"], value["max_left"])
            for axis in [self.right_axis, self.top_right_axis]:
                axis.set_ylim(value["min_right"], value["max_right"])
        except ValueError:
            message = _("Error setting limits, one of the values was "
                        "probably infinite")
            self.application.main_window.add_toast(message)
            logging.exception(message)

    def set_axis_properties(self):
        """Set the properties that are related to the axes."""
        plot_settings = self.application.plot_settings
        self.title = self.axis.set_title(plot_settings.title)
        self.bottom_label = self.axis.set_xlabel(plot_settings.xlabel)
        self.right_label = self.right_axis.set_ylabel(
            plot_settings.right_label)
        self.top_label = self.top_left_axis.set_xlabel(plot_settings.top_label)
        self.left_label = self.axis.set_ylabel(plot_settings.ylabel)
        self.axis.set_xscale(plot_settings.xscale)
        self.axis.set_yscale(plot_settings.yscale)
        self.right_axis.set_xscale(plot_settings.xscale)
        self.right_axis.set_yscale(plot_settings.right_scale)
        self.top_left_axis.set_xscale(plot_settings.top_scale)
        self.top_left_axis.set_yscale(plot_settings.yscale)
        self.top_right_axis.set_xscale(plot_settings.top_scale)
        self.top_right_axis.set_yscale(plot_settings.right_scale)

    def set_ticks(self):
        """Set the tick parameters for the axes in the plot"""
        bottom = pyplot.rcParams["xtick.bottom"]
        left = pyplot.rcParams["ytick.left"]
        top = pyplot.rcParams["xtick.top"]
        right = pyplot.rcParams["ytick.right"]
        ticks = "both" if pyplot.rcParams["xtick.minor.visible"] else "major"
        used_axes = utilities.get_used_axes(self.application)[0]

        # Define axes and their directions
        axes = {
            self.axis: ["bottom", "left"],
            self.top_right_axis: ["top", "right"],
            self.top_left_axis: ["top", "left"],
            self.right_axis: ["bottom", "right"],
        }

        for axis, directions in axes.items():
            # Set tick where requested, as long as that axis is not occupied
            tick_params = {
                "bottom": bottom and (
                    "bottom" in directions or not used_axes["bottom"]),
                "left": left and (
                    "left" in directions or not used_axes["left"]),
                "top": top and (
                    "top" in directions or not used_axes["top"]),
                "right": right and (
                    "right" in directions or not used_axes["right"]),
            }
            axis.tick_params(which=ticks, **tick_params)

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
        items = {self.title, self.top_label, self.bottom_label,
                 self.left_label, self.right_label}
        for item in items:
            if item.contains(event)[0]:
                RenameWindow(self.application, item)

    # Overwritten function - do not change name
    def _post_draw(self, _widget, context):
        """
        Override with custom implementation of rubberband to allow for custom
        rubberband style
        """
        if self._rubberband_rect is not None:
            self.draw_rubberband(context)

    def draw_rubberband(self, context):
        line_width = 1
        if not self._context_is_scaled:
            x_0, y_0, width, height = (dim / self.device_pixel_ratio
                                       for dim in self._rubberband_rect)
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

    def set_legend(self):
        """Set the legend of the graph"""
        if self.application.plot_settings.legend:
            self.legends = []
            lines1, labels1 = self.axis.get_legend_handles_labels()
            lines2, labels2 = self.right_axis.get_legend_handles_labels()
            lines3, labels3 = self.top_left_axis.get_legend_handles_labels()
            lines4, labels4 = self.top_right_axis.get_legend_handles_labels()
            new_lines = lines1 + lines2 + lines3 + lines4
            new_labels = labels1 + labels2 + labels3 + labels4
            labels = \
                [utilities.shorten_label(label, 40) for label in new_labels]
            if labels:
                self.top_right_axis.legend(
                    new_lines, labels,
                    loc=self.application.plot_settings.legend_position,
                    frameon=True, reverse=True)
                return
        if self.top_right_axis.get_legend() is not None:
            self.top_right_axis.get_legend().remove()


class DummyToolbar(NavigationToolbar2):
    """Own implementation of NavigationToolbar2 for rubberband support."""
    # Overwritten function - do not change name
    def _zoom_pan_handler(self, event):
        if event.button != 1:
            return
        if self.canvas.application.interaction_mode == InteractionMode.PAN:
            if event.name == "button_press_event":
                self.press_pan(event)
            elif event.name == "button_release_event":
                self.release_pan(event)
        elif self.canvas.application.interaction_mode == InteractionMode.ZOOM:
            if event.name == "button_press_event":
                self.press_zoom(event)
            elif event.name == "button_release_event":
                self.release_zoom(event)

    # Overwritten function - do not change name
    def _update_cursor(self, event):
        mode = self.canvas.application.interaction_mode
        if event.inaxes and event.inaxes.get_navigate():
            if (mode == InteractionMode.ZOOM
                    and self._last_cursor != tools.Cursors.SELECT_REGION):
                self.canvas.set_cursor(tools.Cursors.SELECT_REGION)
                self._last_cursor = tools.Cursors.SELECT_REGION
            elif (mode == InteractionMode.PAN
                  and self._last_cursor != tools.Cursors.MOVE):
                self.canvas.set_cursor(tools.Cursors.MOVE)
                self._last_cursor = tools.Cursors.MOVE
        elif self._last_cursor != tools.Cursors.POINTER:
            self.canvas.set_cursor(tools.Cursors.POINTER)
            self._last_cursor = tools.Cursors.POINTER

    # Overwritten function - do not change name
    def draw_rubberband(self, _event, x0, y0, x1, y1):
        self.canvas._rubberband_rect = [int(val) for val in (x0,
                                        self.canvas.figure.bbox.height - y0,
                                        x1 - x0, y0 - y1)]
        self.canvas.queue_draw()

    # Overwritten function - do not change name
    def remove_rubberband(self):
        self.canvas._rubberband_rect = None
        self.canvas.queue_draw()

    # Overwritten function - do not change name
    def push_current(self):
        self.canvas.apply_limits()
        self.canvas.application.ViewClipboard.add()

    # Overwritten function - do not change name
    def save_figure(self):
        pass


class Highlight(SpanSelector):
    def __init__(self, canvas, span=None):
        """
        Create a span selector object, to highlight part of the graph.
        If a span already exists, make it visible instead
        """
        super().__init__(
            canvas.top_right_axis,
            lambda x, y: self.on_define(canvas),
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
        if span is not None:
            self.extents = span

    def on_define(self, canvas):
        """
        This ensures that the span selector doesn"t go out of range
        There are some obscure cases where this otherwise happens, and the
        selection tool becomes unusable.
        """
        xmin = min(canvas.top_right_axis.get_xlim())
        xmax = max(canvas.top_right_axis.get_xlim())
        extend_min = self.extents[0]
        extend_max = self.extents[1]
        if self.extents[0] < xmin:
            extend_min = xmin
        if self.extents[1] > xmax:
            extend_max = xmax
        self.extents = (extend_min, extend_max)

    def get_start_stop(self, bottom_x):
        if bottom_x:
            xlim = self.canvas.axis.get_xlim()
            top_lim = self.canvas.top_left_axis.get_xlim()
            xrange_bottom = max(xlim) - min(xlim)
            xrange_top = max(top_lim) - min(top_lim)
            # Run into issues if the range is different, so we calculate this
            # by getting what fraction of top axis is highlighted
            if self.canvas.top_left_axis.get_xscale() == "log":
                fraction_left_limit = utilities.get_fraction_at_value(
                    min(self.extents), min(top_lim), max(top_lim))
                fraction_right_limit = utilities.get_fraction_at_value(
                    max(self.extents), min(top_lim), max(top_lim))
            elif self.canvas.top_left_axis.get_xscale() == "linear":
                fraction_left_limit = \
                    (min(self.extents) - min(top_lim)) / (xrange_top)
                fraction_right_limit = \
                    (max(self.extents) - min(top_lim)) / (xrange_top)

            # Use the fraction that is higlighted on top to calculate to what
            # values this corresponds on bottom axis
            if self.canvas.axis.get_xscale() == "log":
                startx = utilities.get_value_at_fraction(
                    fraction_left_limit, min(xlim), max(xlim))
                stopx = utilities.get_value_at_fraction(
                    fraction_right_limit, min(xlim), max(xlim))
            elif self.canvas.axis.get_xscale() == "linear":
                startx = min(xlim) + xrange_bottom * fraction_left_limit
                stopx = min(xlim) + xrange_bottom * fraction_right_limit
        else:
            startx = min(self.extents)
            stopx = max(self.extents)
        return startx, stopx
