# SPDX-License-Identifier: GPL-3.0-or-later
import time

from cycler import cycler

from gi.repository import Adw

from graphs import plotting_tools, utilities, plot_styles, file_io
from graphs.rename import RenameWindow

from matplotlib import pyplot
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends.backend_gtk4cairo import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector


class Canvas(FigureCanvas):
    """Create the graph widget"""
    def __init__(self, parent):
        self.parent = parent
        style_path = plot_styles.get_user_styles(
            self.parent)[self.parent.plot_settings.plot_style]
        pyplot.style.use(style_path)
        self.style = file_io.get_style(style_path)
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
        self.set_color_cycle()
        self.set_ticks()
        color_rgba = utilities.lookup_color(parent, "accent_color")
        self.rubberband_edge_color = utilities.rgba_to_tuple(color_rgba, True)
        color_rgba.alpha = 0.3
        self.rubberband_fill_color = utilities.rgba_to_tuple(color_rgba, True)
        super().__init__(self.figure)
        self.legends = []
        for axis in [self.right_axis, self.top_left_axis,
                     self.top_right_axis]:
            axis.get_xaxis().set_visible(False)
            axis.get_yaxis().set_visible(False)
        self.dummy_toolbar = DummyToolbar(self)
        self.highlight = Highlight(self)

    def plot(self, item, selected):
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
        if selected:
            linewidth = item.selected_line_thickness
            linestyle = item.linestyle_selected
            marker = item.selected_markers
            marker_size = item.selected_marker_size
        else:
            linewidth = item.unselected_line_thickness
            linestyle = item.linestyle_unselected
            marker = item.unselected_markers
            marker_size = item.unselected_marker_size
        axis.plot(
            item.xdata, item.ydata, linewidth=linewidth, label=item.name,
            linestyle=linestyle, marker=marker, color=item.color,
            markersize=marker_size)
        self.set_legend()

    def set_axis_properties(self):
        """Set the properties that are related to the axes."""
        plot_settings = self.parent.plot_settings
        self.title = self.axis.set_title(plot_settings.title)
        font_weight = self.style["font.weight"]
        self.bottom_label = self.axis.set_xlabel(
            plot_settings.xlabel,
            fontweight=font_weight)
        self.right_label = self.right_axis.set_ylabel(
            plot_settings.right_label,
            fontweight=font_weight)
        self.top_label = self.top_left_axis.set_xlabel(
            plot_settings.top_label,
            fontweight=font_weight)
        self.left_label = self.axis.set_ylabel(
            plot_settings.ylabel,
            fontweight=font_weight)
        self.axis.set_yscale(plot_settings.yscale)
        self.right_axis.set_yscale(plot_settings.right_scale)
        self.top_left_axis.set_xscale(plot_settings.top_scale)
        self.top_right_axis.set_xscale(plot_settings.top_scale)
        self.axis.set_xscale(plot_settings.xscale)

    def set_ticks(self):
        used_axes = utilities.get_used_axes(self.parent)[0]
        bottom = self.style["xtick.bottom"] == "True"
        left = self.style["ytick.left"] == "True"
        top = self.style["xtick.top"] == "True"
        right = self.style["ytick.right"] == "True"
        minor = self.style["xtick.minor.visible"] == "True"
        for axis in [self.top_right_axis,
                     self.top_left_axis, self.axis, self.right_axis]:
            axis.tick_params(bottom=bottom, left=left, top=top, right=right)
            if minor:
                axis.minorticks_on()

    def set_color_cycle(self):
        """Set the color cycle that will be used for the graphs."""
        cmap = self.parent.preferences.config["plot_color_cycle"]
        if Adw.StyleManager.get_default().get_dark() and \
                self.parent.preferences.config["plot_invert_color_cycle_dark"]:
            cmap += "_r"
        self.color_cycle = \
            cycler(color=pyplot.get_cmap(cmap).colors).by_key()["color"]

    # Overwritten function - do not change name
    def __call__(self, event):
        """
        The function is called when a user clicks on it.
        If two clicks are performed close to each other, it registers as a
        double click, and if these were on a specific item (e.g. the title) it
        triggers a dialog to edit this item.

        Unfortunately the GTK Doubleclick signal doesn"t work with matplotlib
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
                RenameWindow(self.parent, item)

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
        if self.parent.plot_settings.legend:
            self.legends = []
            lines1, labels1 = self.axis.get_legend_handles_labels()
            lines2, labels2 = self.right_axis.get_legend_handles_labels()
            lines3, labels3 = self.top_left_axis.get_legend_handles_labels()
            lines4, labels4 = self.top_right_axis.get_legend_handles_labels()
            new_lines = lines1 + lines2 + lines3 + lines4
            new_labels = labels1 + labels2 + labels3 + labels4
            labels = []
            for label in new_labels:
                labels.append(utilities.shorten_label(label, 40))
            if labels:
                self.top_right_axis.legend(
                    new_lines, labels, loc=0, frameon=True)

    def set_limits(self):
        """Set the canvas limits for each axis that is present"""
        used_axes, items = utilities.get_used_axes(self.parent)
        axes = {
            "left": self.axis.get_yscale(),
            "right": self.right_axis.get_yscale(),
            "top": self.top_left_axis.get_xscale(),
            "bottom": self.axis.get_xscale()
        }
        limits = {}
        for position, scale in axes.items():
            limits[position] = plotting_tools.find_limits(
                scale, items[position])
        if used_axes["left"]:
            if used_axes["bottom"]:
                plotting_tools.set_axis_limits(
                    limits["left"], self.axis, axis_type="Y")
                plotting_tools.set_axis_limits(
                    limits["bottom"], self.axis, axis_type="X")
            if used_axes["top"]:
                plotting_tools.set_axis_limits(
                    limits["left"], self.top_left_axis, axis_type="Y")
                plotting_tools.set_axis_limits(
                    limits["top"], self.top_left_axis, axis_type="X")
        if used_axes["right"]:
            if used_axes["bottom"]:
                plotting_tools.set_axis_limits(
                    limits["right"], self.right_axis, axis_type="Y")
                plotting_tools.set_axis_limits(
                    limits["bottom"], self.right_axis, axis_type="X")
            if used_axes["top"]:
                plotting_tools.set_axis_limits(
                    limits["right"], self.top_right_axis, axis_type="Y")
                plotting_tools.set_axis_limits(
                    limits["top"], self.top_right_axis, axis_type="X")


class DummyToolbar(NavigationToolbar2):
    """Own implementation of NavigationToolbar2 for rubberband support."""
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

    def save_figure(self):
        raise NotImplementedError


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
                "linewidth": 1
            },
            handle_props={"linewidth": 0},
            interactive=True,
            drag_from_anywhere=True
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
