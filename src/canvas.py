# SPDX-License-Identifier: GPL-3.0-or-later
import time

from cycler import cycler

from gi.repository import Adw

from graphs import plotting_tools, utilities
from graphs.rename_label import RenameLabelWindow

import matplotlib.pyplot as pyplot
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends.backend_gtk4cairo import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector


class Canvas(FigureCanvas):
    """Create the graph widget"""
    def __init__(self, parent):
        self.figure = Figure()
        self.figure.set_tight_layout(True)
        self.one_click_trigger = False
        self.time_first_click = 0
        self.parent = parent
        self.mpl_connect("button_release_event", self)
        self.set_style(parent)
        self.ax = self.figure.add_subplot(111)
        self.right_axis = self.ax.twinx()
        self.top_left_axis = self.ax.twiny()
        self.top_right_axis = self.top_left_axis.twinx()
        self.set_ax_properties(parent)
        self.set_save_properties(parent)
        self.set_color_cycle(parent)
        self.rubberband_color = utilities.lookup_color(parent, "accent_color")
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
                axis = self.ax
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
            item.xdata, item.ydata, linewidth=linewidth, label=item.filename,
            linestyle=linestyle, marker=marker, color=item.color,
            markersize=marker_size)
        self.set_legend()
        
    def set_save_properties(self, parent):
        """
        Set the properties that are related to saving the figure. Currently
        limited to savefig, but will include the background colour soon.
        """
        pyplot.rcParams["savefig.format"] = \
            parent.preferences.config["savefig_filetype"]
        pyplot.rcParams["savefig.transparent"] = \
            parent.preferences.config["savefig_transparent"]

    def set_ax_properties(self, parent):
        """Set the properties that are related to the axes."""
        self.title = self.ax.set_title(parent.plot_settings.title)
        self.bottom_label = self.ax.set_xlabel(
            parent.plot_settings.xlabel,
            fontweight=parent.plot_settings.font_weight)
        self.right_label = self.right_axis.set_ylabel(
            parent.plot_settings.right_label,
            fontweight=parent.plot_settings.font_weight)
        self.top_label = self.top_left_axis.set_xlabel(
            parent.plot_settings.top_label,
            fontweight=parent.plot_settings.font_weight)
        self.left_label = self.ax.set_ylabel(
            parent.plot_settings.ylabel,
            fontweight=parent.plot_settings.font_weight)
        self.ax.set_yscale(parent.plot_settings.yscale)
        self.right_axis.set_yscale(parent.plot_settings.right_scale)
        self.top_left_axis.set_xscale(parent.plot_settings.top_scale)
        self.top_right_axis.set_xscale(parent.plot_settings.top_scale)
        self.ax.set_xscale(parent.plot_settings.xscale)
        self.set_ticks(parent)

    def set_ticks(self, parent):
        """Set the ticks that are to be used in the graph."""
        for axis in [self.top_right_axis,
                     self.top_left_axis, self.ax, self.right_axis]:
            axis.tick_params(
                direction=parent.plot_settings.tick_direction,
                length=parent.plot_settings.major_tick_length,
                width=parent.plot_settings.major_tick_width, which="major")
            axis.tick_params(
                direction=parent.plot_settings.tick_direction,
                length=parent.plot_settings.minor_tick_length,
                width=parent.plot_settings.minor_tick_width, which="minor")
            axis.tick_params(axis="x", which="minor")
            axis.tick_params(axis="y", which="minor")
            axis.minorticks_on()
            top = False
            bottom = False
            left = False
            right = False
            for key in parent.datadict.keys():
                if parent.datadict[key].plot_x_position == "top":
                    top = True
                if parent.datadict[key].plot_x_position == "bottom":
                    bottom = True
                if parent.datadict[key].plot_y_position == "left":
                    left = True
                if parent.datadict[key].plot_y_position == "right":
                    right = True
            if not (top and bottom):
                axis.tick_params(
                    which="both",
                    bottom=parent.plot_settings.tick_bottom,
                    top=parent.plot_settings.tick_top)
            if not (left and right):
                axis.tick_params(
                    which="both",
                    left=parent.plot_settings.tick_left,
                    right=parent.plot_settings.tick_right)

    def set_style(self, parent):
        """Set the plot style."""
        pyplot.rcParams.update(pyplot.rcParamsDefault)
        if Adw.StyleManager.get_default().get_dark():
            self.figure.patch.set_facecolor("#242424")
            text_color = "white"
        else:
            self.figure.patch.set_facecolor("#fafafa")
            text_color = "black"
        params = {
            "font.weight": parent.plot_settings.font_weight,
            "font.sans-serif": parent.plot_settings.font_family,
            "font.size": parent.plot_settings.font_size,
            "axes.labelsize": parent.plot_settings.font_size,
            "xtick.labelsize": parent.plot_settings.font_size,
            "ytick.labelsize": parent.plot_settings.font_size,
            "axes.titlesize": parent.plot_settings.font_size,
            "legend.fontsize": parent.plot_settings.font_size,
            "font.style": parent.plot_settings.font_style,
            "mathtext.default": "regular",
            "axes.labelcolor": text_color,
        }
        pyplot.style.use(parent.plot_settings.plot_style)
        pyplot.rcParams.update(params)

    def set_color_cycle(self, parent):
        """Set the color cycle that will be used for the graphs."""
        cmap = parent.preferences.config["plot_color_cycle"]
        reverse_dark = parent.preferences.config[
            "plot_invert_color_cycle_dark"]
        if Adw.StyleManager.get_default().get_dark() and reverse_dark:
            cmap += "_r"
        color_cycle = cycler(color=pyplot.get_cmap(cmap).colors)
        self.color_cycle = color_cycle.by_key()["color"]

    def __call__(self, event):
        """
        The function is called when a user clicks on it.
        If two clicks are performed close to each other, it registers as a
        double click, and if these were on a specific item (e.g. the title) it
        triggers a dialog to edit this item.

        Unfortunately the GTK Doubleclick signal doesn"t work with matplotlib
        hence this custom function.
        """
        double_click = False
        if not self.one_click_trigger:
            self.one_click_trigger = True
            self.time_first_click = time.time()
        else:
            double_click_interval = time.time() - self.time_first_click
            if double_click_interval > 0.5:
                self.one_click_trigger = True
                self.time_first_click = time.time()
            else:
                self.one_click_trigger = False
                self.time_first_click = 0
                double_click = True

        if self.title.contains(event)[0] and double_click:
            RenameLabelWindow(self.parent, self.title)
        if self.top_label.contains(event)[0] and double_click:
            RenameLabelWindow(self.parent, self.top_label)
        if self.bottom_label.contains(event)[0] and double_click:
            RenameLabelWindow(self.parent, self.bottom_label)
        if self.left_label.contains(event)[0] and double_click:
            RenameLabelWindow(self.parent, self.left_label)
        if self.right_label.contains(event)[0] and double_click:
            RenameLabelWindow(self.parent, self.right_label)

    def _post_draw(self, _widget, context):
        """
        Override with custom implementation of rubberband to allow for custom
        rubberband style
        """
        if self._rubberband_rect is None:
            return

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
        color = self.rubberband_color
        context.set_source_rgba(color.red, color.green, color.blue, 0.3)
        context.fill()
        context.rectangle(x_0, y_0, width, height)
        context.set_source_rgba(color.red, color.green, color.blue, 1)
        context.stroke()

    def set_legend(self):
        """Set the legend of the graph"""
        if self.parent.plot_settings.legend:
            self.legends = []
            lines1, labels1 = self.ax.get_legend_handles_labels()
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
        used_axes, item_list = plotting_tools.get_used_axes(self.parent)
        """Set the canvas limits for each axis that is present"""
        for axis in used_axes:
            if axis == "left":
                left_items = []
                for key in item_list["left"]:
                    left_items.append(key)
                left_limits = plotting_tools.find_limits(
                    self.parent, self.ax.get_yscale(), left_items)
            if axis == "right":
                right_items = []
                for key in item_list["right"]:
                    right_items.append(key)
                right_limits = plotting_tools.find_limits(
                    self, self.right_axis.get_yscale(), right_items)
            if axis == "top":
                top_items = []
                for key in item_list["top"]:
                    top_items.append(key)
                top_limits = plotting_tools.find_limits(
                    self.parent, axis, top_items)
            if axis == "bottom":
                bottom_items = []
                for key in item_list["bottom"]:
                    bottom_items.append(key)
                bottom_limits = plotting_tools.find_limits(
                    self.parent, axis, bottom_items)
        if used_axes["left"] and used_axes["bottom"]:
            plotting_tools.set_canvas_limits(
                left_limits, self.ax, axis_type="Y")
            plotting_tools.set_canvas_limits(
                bottom_limits, self.ax, axis_type="X")
        if used_axes["left"] and used_axes["top"]:
            plotting_tools.set_canvas_limits(
                left_limits, self.top_left_axis, axis_type="Y")
            plotting_tools.set_canvas_limits(
                top_limits, self.top_left_axis, axis_type="X")
        if used_axes["right"] and used_axes["bottom"]:
            plotting_tools.set_canvas_limits(
                right_limits, self.right_axis, axis_type="Y")
            plotting_tools.set_canvas_limits(
                bottom_limits, self.right_axis, axis_type="X")
        if used_axes["right"] and used_axes["top"]:
            plotting_tools.set_canvas_limits(
                right_limits, self.top_right_axis, axis_type="Y")
            plotting_tools.set_canvas_limits(
                top_limits, self.top_right_axis, axis_type="X")


class DummyToolbar(NavigationToolbar2):
    """Own implementation of NavigationToolbar2 for rubberband support."""
    def draw_rubberband(self, _event, x0, y0, x1, y1):
        self.canvas._rubberband_rect = [int(val) for val in (x0,
                                        self.canvas.figure.bbox.height - y0,
                                        x1 - x0, y0 - y1)]
        self.canvas.queue_draw()

    def remove_rubberband(self):
        self.canvas._rubberband_rect = None
        self.canvas.queue_draw()


class Highlight(SpanSelector):
    def __init__(self, canvas, span=None):
        """
        Create a span selector object, to highlight part of the graph.
        If a span already exists, make it visible instead
        """
        color = canvas.rubberband_color
        super().__init__(
            canvas.top_right_axis,
            lambda x, y: self.on_define(canvas),
            "horizontal",
            useblit=True,
            props={
                "facecolor": (color.red, color.green, color.blue, 0.3),
                "edgecolor": (color.red, color.green, color.blue, 1),
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
            xrange_bottom = max(self.canvas.ax.get_xlim()) \
                - min(self.canvas.ax.get_xlim())
            xrange_top = max(self.canvas.top_left_axis.get_xlim()) \
                - min(self.canvas.top_left_axis.get_xlim())
            # Run into issues if the range is different, so we calculate this
            # by getting what fraction of top axis is highlighted
            if self.canvas.top_left_axis.get_xscale() == "log":
                fraction_left_limit = utilities.get_fraction_at_value(
                    min(self.extents),
                    min(self.canvas.top_left_axis.get_xlim()),
                    max(self.canvas.top_left_axis.get_xlim()))
                fraction_right_limit = utilities.get_fraction_at_value(
                    max(self.extents),
                    min(self.canvas.top_left_axis.get_xlim()),
                    max(self.canvas.top_left_axis.get_xlim()))
            elif self.canvas.top_left_axis.get_xscale() == "linear":
                fraction_left_limit = (
                    min(self.extents) - min(
                        self.canvas.top_left_axis.get_xlim())) / (xrange_top)
                fraction_right_limit = (
                    max(self.extents) - min(
                        self.canvas.top_left_axis.get_xlim())) / (xrange_top)

            # Use the fraction that is higlighted on top to calculate to what
            # values this corresponds on bottom axis
            if self.canvas.ax.get_xscale() == "log":
                startx = utilities.get_value_at_fraction(
                    fraction_left_limit,
                    min(self.canvas.ax.get_xlim()),
                    max(self.canvas.ax.get_xlim()))
                stopx = utilities.get_value_at_fraction(
                    fraction_right_limit,
                    min(self.canvas.ax.get_xlim()),
                    max(self.canvas.ax.get_xlim()))
            elif self.canvas.ax.get_xscale() == "linear":
                xlim = min(self.canvas.ax.get_xlim())
                startx = xlim + xrange_bottom * fraction_left_limit
                stopx = xlim + xrange_bottom * fraction_right_limit
        else:
            startx = min(self.extents)
            stopx = max(self.extents)
        return startx, stopx
