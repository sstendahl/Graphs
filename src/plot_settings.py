# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

from graphs import (clipboard, graphs, misc, plot_styles, plotting_tools, ui,
                    utilities)
from graphs.canvas import Canvas

from matplotlib import pyplot


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/plot_settings.ui")
class PlotSettingsWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PlotSettingsWindow"
    plot_title = Gtk.Template.Child()
    plot_x_label = Gtk.Template.Child()
    plot_y_label = Gtk.Template.Child()
    plot_top_label = Gtk.Template.Child()
    plot_right_label = Gtk.Template.Child()
    plot_x_scale = Gtk.Template.Child()
    plot_y_scale = Gtk.Template.Child()
    plot_top_scale = Gtk.Template.Child()
    plot_right_scale = Gtk.Template.Child()
    plot_legend = Gtk.Template.Child()
    plot_legend_position = Gtk.Template.Child()
    use_custom_plot_style = Gtk.Template.Child()
    custom_plot_style = Gtk.Template.Child()
    min_left = Gtk.Template.Child()
    max_left = Gtk.Template.Child()
    min_bottom = Gtk.Template.Child()
    max_bottom = Gtk.Template.Child()
    min_right = Gtk.Template.Child()
    max_right = Gtk.Template.Child()
    min_top = Gtk.Template.Child()
    max_top = Gtk.Template.Child()
    no_data_message = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        plot_settings = parent.plot_settings
        self.plot_title.set_text(plot_settings.title)
        self.min_left.set_text(str(plot_settings.min_left))
        self.max_left.set_text(str(plot_settings.max_left))
        self.min_bottom.set_text(str(plot_settings.min_bottom))
        self.max_bottom.set_text(str(plot_settings.max_bottom))
        self.min_right.set_text(str(plot_settings.min_right))
        self.max_right.set_text(str(plot_settings.max_right))
        self.min_top.set_text(str(plot_settings.min_top))
        self.max_top.set_text(str(plot_settings.max_top))

        self.plot_x_label.set_text(plot_settings.xlabel)
        self.plot_y_label.set_text(plot_settings.ylabel)
        self.plot_top_label.set_text(plot_settings.top_label)
        self.plot_right_label.set_text(plot_settings.right_label)
        utilities.populate_chooser(self.plot_x_scale, misc.SCALES)
        utilities.set_chooser(self.plot_x_scale, plot_settings.xscale)
        utilities.populate_chooser(self.plot_y_scale, misc.SCALES)
        utilities.set_chooser(self.plot_y_scale, plot_settings.yscale)
        utilities.populate_chooser(self.plot_top_scale, misc.SCALES)
        utilities.set_chooser(self.plot_top_scale, plot_settings.top_scale)
        utilities.populate_chooser(self.plot_right_scale, misc.SCALES)
        utilities.set_chooser(self.plot_right_scale, plot_settings.right_scale)
        self.use_custom_plot_style.set_enable_expansion(
            plot_settings.use_custom_plot_style)
        utilities.populate_chooser(
            self.custom_plot_style, plot_styles.get_user_styles(parent).keys(),
            translate=False)
        utilities.set_chooser(
            self.custom_plot_style, plot_settings.custom_plot_style)
        self.plot_legend.set_enable_expansion(plot_settings.legend)
        utilities.populate_chooser(
            self.plot_legend_position, misc.LEGEND_POSITIONS)
        utilities.set_chooser(
            self.plot_legend_position,
            plot_settings.legend_position.capitalize())
        self.hide_unused_axes_limits(parent)
        if len(parent.datadict) > 0:
            self.no_data_message.set_visible(False)
        self.connect("close-request", self.on_close, parent)
        self.set_transient_for(parent.main_window)
        self.present()

    def hide_unused_axes_limits(self, parent):
        used_axes = utilities.get_used_axes(parent)[0]
        if not used_axes["left"]:
            self.min_left.set_visible(False)
            self.max_left.set_visible(False)
        if not used_axes["right"]:
            self.min_right.set_visible(False)
            self.max_right.set_visible(False)
        if not used_axes["top"]:
            self.min_top.set_visible(False)
            self.max_top.set_visible(False)
        if not used_axes["bottom"]:
            self.min_bottom.set_visible(False)
            self.max_bottom.set_visible(False)

    def on_close(self, _, parent):
        plot_settings = parent.plot_settings

        # Check if style change when override is enabled
        self.style_changed = \
            plot_settings.use_custom_plot_style \
            != self.use_custom_plot_style.get_enable_expansion() \
            and parent.preferences.config["override_style_change"] \
            or plot_settings.custom_plot_style \
            != utilities.get_selected_chooser_item(self.custom_plot_style) \
            and parent.preferences.config["override_style_change"]

        # Set new plot settings
        plot_settings.title = self.plot_title.get_text()
        plot_settings.xlabel = self.plot_x_label.get_text()
        plot_settings.ylabel = self.plot_y_label.get_text()
        plot_settings.top_label = self.plot_top_label.get_text()
        plot_settings.right_label = self.plot_right_label.get_text()
        plot_settings.xscale = \
            utilities.get_selected_chooser_item(self.plot_x_scale)
        plot_settings.yscale = \
            utilities.get_selected_chooser_item(self.plot_y_scale)
        plot_settings.top_scale = \
            utilities.get_selected_chooser_item(self.plot_top_scale)
        plot_settings.right_scale = \
            utilities.get_selected_chooser_item(self.plot_right_scale)
        plot_settings.legend = self.plot_legend.get_enable_expansion()
        plot_settings.legend_position = \
            utilities.get_selected_chooser_item(
                self.plot_legend_position).lower()
        plot_settings.use_custom_plot_style = \
            self.use_custom_plot_style.get_enable_expansion()
        plot_settings.custom_plot_style = \
            utilities.get_selected_chooser_item(self.custom_plot_style)

        plot_settings.min_bottom = float(self.min_bottom.get_text())
        plot_settings.max_bottom = float(self.max_bottom.get_text())
        plot_settings.min_top = float(self.min_top.get_text())
        plot_settings.max_top = float(self.max_top.get_text())
        plot_settings.min_left = float(self.min_left.get_text())
        plot_settings.max_left = float(self.max_left.get_text())
        plot_settings.mix_right = float(self.min_right.get_text())
        plot_settings.max_right = float(self.max_right.get_text())

        # Set new item properties
        if self.style_changed:
            parent.canvas = Canvas(parent=parent)
            for item in parent.datadict.values():
                item.color = None
            for item in parent.datadict.values():
                item.color = plotting_tools.get_next_color(parent)
                item.linestyle = pyplot.rcParams["lines.linestyle"]
                item.linewidth = float(pyplot.rcParams["lines.linewidth"])
                item.markerstyle = pyplot.rcParams["lines.marker"]
                item.markersize = \
                    float(pyplot.rcParams["lines.markersize"])
            clipboard.add(parent)

        # Reload UI
        ui.reload_item_menu(parent)
        graphs.reload(parent)
