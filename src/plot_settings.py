# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

from graphs import graphs, plotting_tools, utilities

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/plot_settings.ui")
class PlotSettingsWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PlotSettingsWindow"
    datalist_chooser = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    linestyle_selected = Gtk.Template.Child()
    linestyle_unselected = Gtk.Template.Child()
    selected_line_thickness_slider = Gtk.Template.Child()
    unselected_line_thickness_slider = Gtk.Template.Child()
    selected_markers_chooser = Gtk.Template.Child()
    unselected_markers_chooser = Gtk.Template.Child()
    selected_marker_size = Gtk.Template.Child()
    unselected_marker_size = Gtk.Template.Child()
    plot_title = Gtk.Template.Child()
    plot_style = Gtk.Template.Child()
    plot_x_scale = Gtk.Template.Child()
    plot_y_scale = Gtk.Template.Child()
    plot_right_scale = Gtk.Template.Child()
    plot_top_scale = Gtk.Template.Child()
    plot_y_position = Gtk.Template.Child()
    plot_x_position = Gtk.Template.Child()
    plot_y_label = Gtk.Template.Child()
    plot_x_label = Gtk.Template.Child()
    plot_right_label = Gtk.Template.Child()
    plot_top_label = Gtk.Template.Child()
    plot_tick_direction = Gtk.Template.Child()
    plot_major_tick_width = Gtk.Template.Child()
    plot_minor_tick_width = Gtk.Template.Child()
    plot_major_tick_length = Gtk.Template.Child()
    plot_minor_tick_length = Gtk.Template.Child()
    plot_tick_left = Gtk.Template.Child()
    plot_tick_right = Gtk.Template.Child()
    plot_tick_top = Gtk.Template.Child()
    plot_tick_bottom = Gtk.Template.Child()
    plot_legend_check = Gtk.Template.Child()
    plot_font_chooser = Gtk.Template.Child()

    def __init__(self, parent, key=None):
        super().__init__()
        self.select_item = False
        self.chooser_changed = True
        filenames = utilities.get_all_filenames(parent)
        utilities.populate_chooser(self.datalist_chooser, filenames)
        self.item = self.load_config(parent, key)
        self.datalist_chooser.connect(
            "notify::selected", self.on_notify, parent)
        self.connect("close-request", self.on_close, parent)
        self.set_transient_for(parent.main_window)
        self.present()

    def on_notify(self, _, __, parent):
        self.save_settings(parent)
        filenames = utilities.get_all_filenames(parent)
        self.name_entry.set_text("")
        index = self.datalist_chooser.get_selected()
        if set(filenames) != \
                set(utilities.get_chooser_list(self.datalist_chooser)):
            utilities.populate_chooser(self.datalist_chooser, filenames)
        self.datalist_chooser.set_selected(index)
        self.load_config(parent, key=None)
        self.chooser_changed = False

    def load_config(self, parent, key):
        data_list = utilities.get_datalist(parent)
        index = self.datalist_chooser.get_selected()
        if key is not None:
            index = data_list.index(key)
        self.datalist_chooser.set_selected(index)
        item = parent.datadict[data_list[index]]
        font_string = parent.plot_settings.font_string
        font_desc = self.plot_font_chooser.get_font_desc().from_string(
            font_string)
        self.plot_font_chooser.set_font_desc(font_desc)
        self.plot_font_chooser.set_use_font(True)
        self.selected_line_thickness_slider.set_range(0.1, 10)
        self.unselected_line_thickness_slider.set_range(0.1, 10)
        self.selected_marker_size.set_range(0, 30)
        self.unselected_marker_size.set_range(0, 30)
        self.plot_major_tick_width.set_range(0, 4)
        self.plot_minor_tick_width.set_range(0, 4)
        self.plot_major_tick_length.set_range(0, 20)
        self.plot_minor_tick_length.set_range(0, 20)
        self.plot_title.set_text(parent.plot_settings.title)
        self.plot_y_label.set_text(parent.plot_settings.ylabel)
        self.plot_x_label.set_text(parent.plot_settings.xlabel)
        self.plot_right_label.set_text(parent.plot_settings.right_label)
        self.plot_top_label.set_text(parent.plot_settings.top_label)
        self.plot_minor_tick_width.set_value(
            parent.plot_settings.minor_tick_width)
        self.plot_major_tick_width.set_value(
            parent.plot_settings.major_tick_width)
        self.plot_minor_tick_length.set_value(
            parent.plot_settings.minor_tick_length)
        self.plot_major_tick_length.set_value(
            parent.plot_settings.major_tick_length)
        utilities.set_chooser(self.plot_y_position, item.plot_y_position)
        utilities.set_chooser(self.plot_x_position, item.plot_x_position)
        utilities.set_chooser(self.plot_x_scale, parent.plot_settings.xscale)
        utilities.set_chooser(self.plot_y_scale, parent.plot_settings.yscale)
        utilities.set_chooser(
            self.plot_right_scale, parent.plot_settings.right_scale)
        utilities.set_chooser(
            self.plot_top_scale, parent.plot_settings.top_scale)
        utilities.set_chooser(
            self.plot_tick_direction, parent.plot_settings.tick_direction)
        utilities.set_chooser(self.linestyle_selected, item.linestyle_selected)
        utilities.set_chooser(
            self.linestyle_unselected, item.linestyle_unselected)
        self.selected_line_thickness_slider.set_value(
            item.selected_line_thickness)
        self.unselected_line_thickness_slider.set_value(
            item.unselected_line_thickness)
        self.selected_marker_size.set_value(item.selected_marker_size)
        self.unselected_marker_size.set_value(item.unselected_marker_size)
        utilities.populate_chooser(
            self.selected_markers_chooser,
            list(Line2D.markers.values()), clear=False)
        utilities.populate_chooser(self.plot_style, plt.style.available)
        utilities.populate_chooser(
            self.unselected_markers_chooser,
            list(Line2D.markers.values()), clear=False)
        utilities.set_chooser(self.plot_style, parent.plot_settings.plot_style)
        marker_dict = Line2D.markers
        unselected_marker_value = marker_dict[item.unselected_markers]
        selected_marker_value = marker_dict[item.selected_markers]
        utilities.set_chooser(
            self.selected_markers_chooser, selected_marker_value)
        utilities.set_chooser(
            self.unselected_markers_chooser, unselected_marker_value)
        self.item = item
        if parent.plot_settings.tick_left:
            self.plot_tick_left.set_active(True)
        if parent.plot_settings.tick_right:
            self.plot_tick_right.set_active(True)
        if parent.plot_settings.tick_bottom:
            self.plot_tick_bottom.set_active(True)
        if parent.plot_settings.tick_top:
            self.plot_tick_top.set_active(True)
        if parent.plot_settings.legend:
            self.plot_legend_check.set_active(True)
        return item

    def set_config(self, item, parent):
        plot_settings = parent.plot_settings
        font_name = self.plot_font_chooser.get_font_desc(
        ).to_string().lower().split(" ")
        font_size = font_name[-1]
        font_weight = utilities.get_font_weight(font_name)
        font_style = utilities.get_font_style(font_name)
        plot_settings.font_size = font_size
        plot_settings.font_style = font_style
        plot_settings.font_weight = font_weight
        font_description = self.plot_font_chooser.get_font_desc()
        plot_settings.font_string = font_description.to_string()
        plot_settings.font_family = font_description.get_family()
        plot_settings.legend = self.plot_legend_check.get_active()
        plot_settings.title = self.plot_title.get_text()
        plot_settings.tick_left = self.plot_tick_left.get_active()
        plot_settings.tick_right = self.plot_tick_right.get_active()
        plot_settings.tick_top = self.plot_tick_top.get_active()
        plot_settings.tick_bottom = self.plot_tick_bottom.get_active()
        plot_settings.major_tick_width = self.plot_major_tick_width.get_value()
        plot_settings.minor_tick_width = self.plot_minor_tick_width.get_value()
        plot_major_tick_length = self.plot_major_tick_length
        plot_settings.major_tick_length = plot_major_tick_length.get_value()
        plot_minor_tick_length = self.plot_minor_tick_length
        plot_settings.minor_tick_length = plot_minor_tick_length.get_value()
        selected_item = self.plot_tick_direction.get_selected_item()
        plot_settings.tick_direction = selected_item.get_string()
        plot_settings.ylabel = self.plot_y_label.get_text()
        plot_settings.xlabel = self.plot_x_label.get_text()
        plot_settings.right_label = self.plot_right_label.get_text()
        plot_settings.top_label = self.plot_top_label.get_text()
        plot_settings.xscale = self.plot_x_scale.get_selected_item(
        ).get_string()
        plot_settings.yscale = self.plot_y_scale.get_selected_item(
        ).get_string()
        plot_settings.right_scale = self.plot_right_scale.get_selected_item(
        ).get_string()
        plot_settings.top_scale = self.plot_top_scale.get_selected_item(
        ).get_string()
        plot_settings.plot_style = self.plot_style.get_selected_item(
        ).get_string()
        if self.name_entry.get_text() != "":
            item.filename = self.name_entry.get_text()
        item.plot_Y_position = self.plot_y_position.get_selected_item(
        ).get_string()
        item.plot_X_position = self.plot_x_position.get_selected_item(
        ).get_string()
        item.linestyle_selected = self.linestyle_selected.get_selected_item(
        ).get_string()
        linestyle_unselected = self.linestyle_unselected
        item.linestyle_unselected = linestyle_unselected.get_selected_item(
        ).get_string()
        selected_markers = self.selected_markers_chooser
        item.selected_markers = selected_markers.get_selected_item(
        ).get_string()
        unselected_markers = self.unselected_markers_chooser
        item.unselected_markers = unselected_markers.get_selected_item(
        ).get_string()
        selected_slider = self.selected_line_thickness_slider
        item.selected_line_thickness = selected_slider.get_value()
        unselected_slider = self.unselected_line_thickness_slider
        item.unselected_line_thickness = unselected_slider.get_value()
        item.selected_marker_size = self.selected_marker_size.get_value()
        item.unselected_marker_size = self.unselected_marker_size.get_value()
        marker_dict = Line2D.markers
        item.selected_markers = utilities.get_dict_by_value(
            marker_dict,
            self.selected_markers_chooser.get_selected_item().get_string())
        item.unselected_markers = utilities.get_dict_by_value(
            marker_dict,
            self.unselected_markers_chooser.get_selected_item().get_string())
        return item

    def on_close(self, _, parent):
        item = self.item
        new_item = self.set_config(item, parent)
        max_length = int(26)
        if len(new_item.filename) > max_length:
            label = f"{new_item.filename[:max_length]}..."
        else:
            label = new_item.filename
        parent.item_rows[new_item.key].sample_id_label.set_text(label)
        if new_item.selected:
            graphs.select_item(parent, new_item.key)
        plotting_tools.refresh_plot(parent)
