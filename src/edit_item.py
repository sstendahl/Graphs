# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

from graphs import graphs, utilities

from matplotlib.lines import Line2D


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/edit_item.ui")
class EditItemWindow(Adw.PreferencesWindow):
    __gtype_name__ = "EditItemWindow"
    item_selector = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    plot_x_position = Gtk.Template.Child()
    plot_y_position = Gtk.Template.Child()
    linestyle_selected = Gtk.Template.Child()
    linestyle_unselected = Gtk.Template.Child()
    selected_line_thickness_slider = Gtk.Template.Child()
    unselected_line_thickness_slider = Gtk.Template.Child()
    selected_markers_chooser = Gtk.Template.Child()
    unselected_markers_chooser = Gtk.Template.Child()
    selected_marker_size = Gtk.Template.Child()
    unselected_marker_size = Gtk.Template.Child()

    def __init__(self, parent, item):
        super().__init__()
        self.parent = parent
        self.item = item
        filenames = utilities.get_all_filenames(self.parent)
        utilities.populate_chooser(self.item_selector, filenames)
        self.item_selector.set_selected(filenames.index(self.item.filename))
        self.load_values()
        self.item_selector.connect("notify::selected", self.on_select)
        self.connect("close-request", self.apply)
        self.set_transient_for(parent.main_window)
        self.present()

    def on_select(self, _action, _target):
        self.apply(None)
        data_list = list(self.parent.datadict.keys())
        index = self.item_selector.get_selected()
        self.item = self.parent.datadict[data_list[index]]
        self.load_values()

        #If item_selector no longer matches with filename, repopulate it
        index = self.item_selector.get_selected()
        filenames = utilities.get_all_filenames(self.parent)
        if set(filenames) != \
                set(utilities.get_chooser_list(self.item_selector)):
            utilities.populate_chooser(self.item_selector, filenames)
        self.item_selector.set_selected(index)

    def load_values(self):
        marker_dict = Line2D.markers
        self.set_title(self.item.filename)
        self.name_entry.set_text(self.item.filename)
        utilities.set_chooser(
            self.plot_x_position, self.item.plot_x_position)
        utilities.set_chooser(
            self.plot_y_position, self.item.plot_y_position)
        utilities.set_chooser(
            self.linestyle_selected, self.item.linestyle_selected)
        utilities.set_chooser(
            self.linestyle_unselected, self.item.linestyle_unselected)
        self.selected_line_thickness_slider.set_range(0.1, 10)
        self.selected_line_thickness_slider.set_value(
            self.item.selected_line_thickness)
        self.unselected_line_thickness_slider.set_range(0.1, 10)
        self.unselected_line_thickness_slider.set_value(
            self.item.unselected_line_thickness)
        utilities.populate_chooser(
            self.selected_markers_chooser,
            list(Line2D.markers.values()), clear=False)
        utilities.populate_chooser(
            self.unselected_markers_chooser,
            list(Line2D.markers.values()), clear=False)
        utilities.set_chooser(
            self.selected_markers_chooser,
            marker_dict[self.item.selected_markers])
        utilities.set_chooser(
            self.unselected_markers_chooser,
            marker_dict[self.item.unselected_markers])
        self.selected_marker_size.set_range(0, 30)
        self.selected_marker_size.set_value(self.item.selected_marker_size)
        self.unselected_marker_size.set_range(0, 30)
        self.unselected_marker_size.set_value(self.item.unselected_marker_size)

    def apply(self, _):
        self.item.filename = self.name_entry.get_text()
        self.item.plot_x_position = \
            self.plot_x_position.get_selected_item().get_string()
        self.item.plot_y_position = \
            self.plot_y_position.get_selected_item().get_string()
        self.item.linestyle_selected = \
            self.linestyle_selected.get_selected_item().get_string()
        self.item.linestyle_unselected = \
            self.linestyle_unselected.get_selected_item().get_string()
        self.item.selected_line_thickness = \
            self.selected_line_thickness_slider.get_value()
        self.item.unselected_line_thickness = \
            self.unselected_line_thickness_slider.get_value()
        marker_dict = Line2D.markers
        self.item.selected_markers = utilities.get_dict_by_value(
            marker_dict,
            self.selected_markers_chooser.get_selected_item().get_string())
        self.item.unselected_markers = utilities.get_dict_by_value(
            marker_dict,
            self.unselected_markers_chooser.get_selected_item().get_string())
        self.item.selected_marker_size = self.selected_marker_size.get_value()
        self.item.unselected_marker_size = \
            self.unselected_marker_size.get_value()

        self.parent.item_rows[self.item.key].label.set_text(
            utilities.shorten_label(self.item.filename))
        if self.item.selected:
            graphs.select_item(self.parent, self.item.key)
