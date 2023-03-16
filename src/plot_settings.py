# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

from graphs import graphs, utilities

import matplotlib.pyplot as plt


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/plot_settings.ui")
class PlotSettingsWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PlotSettingsWindow"
    plot_title = Gtk.Template.Child()
    plot_x_label = Gtk.Template.Child()
    plot_y_label = Gtk.Template.Child()
    plot_top_label = Gtk.Template.Child()
    plot_right_label = Gtk.Template.Child()
    plot_font_chooser = Gtk.Template.Child()
    plot_x_scale = Gtk.Template.Child()
    plot_y_scale = Gtk.Template.Child()
    plot_top_scale = Gtk.Template.Child()
    plot_right_scale = Gtk.Template.Child()
    plot_tick_direction = Gtk.Template.Child()
    plot_major_tick_width = Gtk.Template.Child()
    plot_minor_tick_width = Gtk.Template.Child()
    plot_major_tick_length = Gtk.Template.Child()
    plot_minor_tick_length = Gtk.Template.Child()
    plot_tick_bottom = Gtk.Template.Child()
    plot_tick_left = Gtk.Template.Child()
    plot_tick_top = Gtk.Template.Child()
    plot_tick_right = Gtk.Template.Child()
    plot_legend_check = Gtk.Template.Child()
    plot_style = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()

        self.plot_title.set_text(parent.plot_settings.title)
        self.plot_x_label.set_text(parent.plot_settings.xlabel)
        self.plot_y_label.set_text(parent.plot_settings.ylabel)
        self.plot_top_label.set_text(parent.plot_settings.top_label)
        self.plot_right_label.set_text(parent.plot_settings.right_label)
        font_string = parent.plot_settings.font_string
        font_desc = self.plot_font_chooser.get_font_desc().from_string(
            font_string)
        self.plot_font_chooser.set_font_desc(font_desc)
        self.plot_font_chooser.set_use_font(True)
        utilities.set_chooser(
            self.plot_x_scale, parent.plot_settings.xscale)
        utilities.set_chooser(
            self.plot_y_scale, parent.plot_settings.yscale)
        utilities.set_chooser(
            self.plot_top_scale, parent.plot_settings.top_scale)
        utilities.set_chooser(
            self.plot_right_scale, parent.plot_settings.right_scale)
        utilities.set_chooser(
            self.plot_tick_direction, parent.plot_settings.tick_direction)
        self.plot_major_tick_width.set_range(0, 4)
        self.plot_major_tick_width.set_value(
            parent.plot_settings.major_tick_width)
        self.plot_minor_tick_width.set_range(0, 4)
        self.plot_minor_tick_width.set_value(
            parent.plot_settings.minor_tick_width)
        self.plot_major_tick_length.set_range(0, 20)
        self.plot_major_tick_length.set_value(
            parent.plot_settings.major_tick_length)
        self.plot_minor_tick_length.set_range(0, 20)
        self.plot_minor_tick_length.set_value(
            parent.plot_settings.minor_tick_length)
        if parent.plot_settings.tick_bottom:
            self.plot_tick_bottom.set_active(True)
        if parent.plot_settings.tick_left:
            self.plot_tick_left.set_active(True)
        if parent.plot_settings.tick_top:
            self.plot_tick_top.set_active(True)
        if parent.plot_settings.tick_right:
            self.plot_tick_right.set_active(True)
        if parent.plot_settings.legend:
            self.plot_legend_check.set_active(True)
        utilities.populate_chooser(self.plot_style, plt.style.available)
        utilities.set_chooser(self.plot_style, parent.plot_settings.plot_style)

        self.connect("close-request", self.on_close, parent)
        self.set_transient_for(parent.main_window)
        self.present()

    def on_close(self, _, parent):
        plot_settings = parent.plot_settings
        plot_settings.title = self.plot_title.get_text()
        plot_settings.xlabel = self.plot_x_label.get_text()
        plot_settings.ylabel = self.plot_y_label.get_text()
        plot_settings.top_label = self.plot_top_label.get_text()
        plot_settings.right_label = self.plot_right_label.get_text()
        font_name = \
            self.plot_font_chooser.get_font_desc()\
            .to_string().lower().split(" ")
        plot_settings.font_size = font_name[-1]
        plot_settings.font_style = utilities.get_font_style(font_name)
        plot_settings.font_weight = utilities.get_font_weight(font_name)
        font_description = self.plot_font_chooser.get_font_desc()
        plot_settings.font_string = font_description.to_string()
        plot_settings.font_family = font_description.get_family()
        plot_settings.xscale = \
            self.plot_x_scale.get_selected_item().get_string()
        plot_settings.yscale = \
            self.plot_y_scale.get_selected_item().get_string()
        plot_settings.top_scale = \
            self.plot_top_scale.get_selected_item().get_string()
        plot_settings.right_scale = \
            self.plot_right_scale.get_selected_item().get_string()
        plot_settings.tick_direction = \
            self.plot_tick_direction.get_selected_item().get_string()
        plot_settings.major_tick_width = self.plot_major_tick_width.get_value()
        plot_settings.minor_tick_width = self.plot_minor_tick_width.get_value()
        plot_settings.tick_bottom = self.plot_tick_bottom.get_active()
        plot_settings.tick_left = self.plot_tick_left.get_active()
        plot_settings.tick_top = self.plot_tick_top.get_active()
        plot_settings.tick_right = self.plot_tick_right.get_active()
        plot_settings.major_tick_length = \
            self.plot_major_tick_length.get_value()
        plot_settings.minor_tick_length = \
            self.plot_minor_tick_length.get_value()
        plot_settings.legend = self.plot_legend_check.get_active()
        plot_settings.plot_style = \
            self.plot_style.get_selected_item().get_string()
        graphs.reload(parent)
