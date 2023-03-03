# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

from graphs import graphs, utilities

from matplotlib.lines import Line2D

@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/edit_item.ui")
class EditItemWindow(Adw.PreferencesWindow):
    __gtype_name__ = "EditItemWindow"
    name_entry = Gtk.Template.Child()
    linestyle_selected = Gtk.Template.Child()
    linestyle_unselected = Gtk.Template.Child()
    selected_line_thickness_slider = Gtk.Template.Child()
    unselected_line_thickness_slider = Gtk.Template.Child()
    selected_markers_chooser = Gtk.Template.Child()
    unselected_markers_chooser = Gtk.Template.Child()
    selected_marker_size = Gtk.Template.Child()
    unselected_marker_size = Gtk.Template.Child()
    plot_y_position = Gtk.Template.Child()
    plot_x_position = Gtk.Template.Child()

    def __init__(self, parent, key):
        super().__init__()
        self.parent = parent
        self.item = parent.datadict[key]

        self.set_title(self.item.filename)
        self.name_entry.set_text(self.item.filename)
        marker_dict = Line2D.markers
        unselected_marker_value = marker_dict[self.item.unselected_markers]
        selected_marker_value = marker_dict[self.item.selected_markers]
        self.selected_line_thickness_slider.set_range(0.1, 10)
        self.unselected_line_thickness_slider.set_range(0.1, 10)
        self.selected_marker_size.set_range(0, 30)
        self.unselected_marker_size.set_range(0, 30)
        utilities.populate_chooser(
            self.selected_markers_chooser,
            list(Line2D.markers.values()), clear=False)
        utilities.populate_chooser(
            self.unselected_markers_chooser,
            list(Line2D.markers.values()), clear=False)
        utilities.set_chooser(
            self.selected_markers_chooser, selected_marker_value)
        utilities.set_chooser(
            self.unselected_markers_chooser, unselected_marker_value)
        utilities.set_chooser(self.plot_y_position, self.item.plot_y_position)
        utilities.set_chooser(self.plot_x_position, self.item.plot_x_position)
        utilities.set_chooser(
            self.linestyle_selected, self.item.linestyle_selected)
        utilities.set_chooser(
            self.linestyle_unselected, self.item.linestyle_unselected)
        self.selected_line_thickness_slider.set_value(
            self.item.selected_line_thickness)
        self.unselected_line_thickness_slider.set_value(
            self.item.unselected_line_thickness)
        self.selected_marker_size.set_value(self.item.selected_marker_size)
        self.unselected_marker_size.set_value(self.item.unselected_marker_size)

        self.connect("close-request", self.on_close)
        self.set_transient_for(parent.main_window)
        self.present()

    def on_close(self, _):
        self.item.filename = self.name_entry.get_text()
        self.item.plot_Y_position = \
            self.plot_y_position.get_selected_item().get_string()
        self.item.plot_X_position = \
            self.plot_x_position.get_selected_item().get_string()
        self.item.linestyle_selected = \
            self.linestyle_selected.get_selected_item().get_string()
        self.item.linestyle_unselected = \
            self.linestyle_unselected.get_selected_item().get_string()
        self.item.selected_markers = \
            self.selected_markers_chooser.get_selected_item().get_string()
        self.item.unselected_markers = \
            self.unselected_markers_chooser.get_selected_item().get_string()
        self.item.selected_line_thickness = \
            self.selected_line_thickness_slider.get_value()
        self.item.unselected_line_thickness = \
            self.unselected_line_thickness_slider.get_value()
        self.item.selected_marker_size = self.selected_marker_size.get_value()
        self.item.unselected_marker_size = \
            self.unselected_marker_size.get_value()
        marker_dict = Line2D.markers
        self.item.selected_markers = utilities.get_dict_by_value(
            marker_dict,
            self.selected_markers_chooser.get_selected_item().get_string())
        self.item.unselected_markers = utilities.get_dict_by_value(
            marker_dict,
            self.unselected_markers_chooser.get_selected_item().get_string())
        max_length = int(26)
        if len(self.item.filename) > max_length:
            label = f"{self.item.filename[:max_length]}..."
        else:
            label = self.item.filename
        self.parent.item_rows[self.item.key].sample_id_label.set_text(label)
        if self.item.selected:
            graphs.select_item(self.parent, self.item.key)
