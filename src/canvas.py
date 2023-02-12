# SPDX-License-Identifier: GPL-3.0-or-later
import time
import matplotlib.pyplot as plt

from gi.repository import Gtk, Adw
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk4cairo import FigureCanvas
from cycler import cycler

from . import rename_label

class Canvas(FigureCanvas):
    rubberband_color_float = [120 / 255, 174 / 255, 237 / 255]
    """
    Create the graph widget
    """
    def __init__(self, parent, xlabel="", ylabel="", yscale = "log", title="", scale="linear", style = "adwaita"):
        self.figure = Figure()
        self.figure.set_tight_layout(True)
        self.one_click_trigger = False
        self.time_first_click  = 0
        self.parent = parent
        self.mpl_connect('button_release_event', self)
        self.set_style(parent)
        self.ax = self.figure.add_subplot(111)
        self.right_axis = self.ax.twinx()
        self.top_left_axis = self.ax.twiny()
        self.top_right_axis = self.top_left_axis.twinx()
        self.set_ax_properties(parent)
        self.set_save_properties(parent)
        self.set_color_cycle(parent)
        super().__init__(self.figure)

    def set_save_properties(self, parent):
        """
        Set the properties that are related to saving the figure. Currently
        limited to savefig, but will include the background colour soon.
        """
        plt.rcParams["savefig.format"] = parent.preferences.config["savefig_filetype"]
        plt.rcParams["savefig.transparent"] = parent.preferences.config["savefig_transparent"]

    def set_ax_properties(self, parent):
        """
        Set the properties that are related to the axes.
        """
        self.title = self.ax.set_title(parent.plot_settings.title)
        self.bottom_label = self.ax.set_xlabel(parent.plot_settings.xlabel, fontweight = parent.plot_settings.font_weight)
        self.right_label = self.right_axis.set_ylabel(parent.plot_settings.right_label, fontweight = parent.plot_settings.font_weight)
        self.top_label = self.top_left_axis.set_xlabel(parent.plot_settings.top_label, fontweight = parent.plot_settings.font_weight)
        self.left_label = self.ax.set_ylabel(parent.plot_settings.ylabel, fontweight = parent.plot_settings.font_weight)
        self.ax.set_yscale(parent.plot_settings.yscale)
        self.right_axis.set_yscale(parent.plot_settings.right_scale)
        self.top_left_axis.set_xscale(parent.plot_settings.top_scale)
        self.top_right_axis.set_xscale(parent.plot_settings.top_scale)
        self.ax.set_xscale(parent.plot_settings.xscale)
        self.set_ticks(parent)

    def set_ticks(self, parent):
        """
        Set the ticks that are to be used in the graph.
        """
        for axis in [self.top_right_axis, self.top_left_axis, self.ax, self.right_axis]:
            axis.tick_params(direction=parent.plot_settings.tick_direction, length=parent.plot_settings.major_tick_length, width=parent.plot_settings.major_tick_width, which="major")
            axis.tick_params(direction=parent.plot_settings.tick_direction, length=parent.plot_settings.minor_tick_length, width=parent.plot_settings.minor_tick_width, which="minor")
            axis.tick_params(axis='x',which='minor')
            axis.tick_params(axis='y',which='minor')
            axis.minorticks_on()
            top = False
            bottom = False
            left = False
            right = False
            for key in parent.datadict.keys():
                if parent.datadict[key].plot_X_position == "top":
                    top = True
                if parent.datadict[key].plot_X_position == "bottom":
                    bottom = True
                if parent.datadict[key].plot_Y_position == "left":
                    left = True
                if parent.datadict[key].plot_Y_position == "right":
                    right = True
            if not (top and bottom):
                axis.tick_params(which = "both", bottom=parent.plot_settings.tick_bottom, top=parent.plot_settings.tick_top)
            if not (left and right):
                axis.tick_params(which = "both", left=parent.plot_settings.tick_left, right=parent.plot_settings.tick_right)

    def set_style(self, parent):
        """
        Set the plot style.
        """
        plt.rcParams.update(plt.rcParamsDefault)
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
        "xtick.color" : text_color,
        "ytick.color" : text_color,
        "axes.labelcolor" : text_color,
        }
        plt.style.use(parent.plot_settings.plot_style)
        plt.rcParams.update(params)

    def set_color_cycle(self, parent):
        """
        Set the color cycle that will be used for the graphs.
        """
        cmap = parent.preferences.config["plot_color_cycle"]
        reverse_dark = parent.preferences.config["plot_invert_color_cycle_dark"]
        if Adw.StyleManager.get_default().get_dark() and reverse_dark:
            cmap += "_r"
        color_cycle = cycler(color=plt.get_cmap(cmap).colors)
        self.color_cycle = color_cycle.by_key()['color']

    def __call__(self, event):
        """
        The function is called when a user clicks on it.
        If two clicks are performed close to each other, it registers as a double
        click, and if these were on a specific item (e.g. the title) it triggers
        a dialog to edit this item.

        Unfortunately the GTK Doubleclick signal doesn't work with matplotlib
        hence this custom function.
        """
        double_click = False
        if self.one_click_trigger == False:
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
            rename_label.open_rename_label_window(self.parent, self.title)
        if self.top_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.top_label)
        if self.bottom_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.bottom_label)
        if self.left_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.left_label)
        if self.right_label.contains(event)[0] and double_click:
            rename_label.open_rename_label_window(self.parent, self.right_label)

    def _post_draw(self, widget, context):
        """
        Override with custom implementation of rubberband to allow for custom rubberband style
        @param context: https://pycairo.readthedocs.io/en/latest/reference/context.html
        """
        if self._rubberband_rect is None:
            return

        lw = 1
        if not self._context_is_scaled:
            x0, y0, w, h = (dim / self.device_pixel_ratio
                            for dim in self._rubberband_rect)
        else:
            x0, y0, w, h = self._rubberband_rect
            lw *= self.device_pixel_ratio
        x1 = x0 + w
        y1 = y0 + h

        context.set_antialias(1)
        context.set_line_width(lw)
        context.rectangle(x0, y0, w, h)
        ca = self.rubberband_color_float
        context.set_source_rgba(ca[0], ca[1], ca[2], 0.2)
        context.fill()
        context.rectangle(x0, y0, w, h)
        context.set_source_rgba(ca[0], ca[1], ca[2], 1)
        context.stroke()

