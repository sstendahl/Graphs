from gi.repository import Gtk, Adw, GObject, Gio
from numpy import *
from . import item_operations, plotting_tools, datman, utilities
from .data import Data
from matplotlib.lines import Line2D

def open_plot_settings(widget, _, self):
    win = PlotSettingsWindow(self)
    name = "transform_confirm"
    button = win.apply_button
    button.connect("clicked", on_accept, self, win)
    win.present()

def on_accept(widget, self, window):
    item = window.item
    new_item, old_filename = window.set_config(item)
    if old_filename != new_item.filename:
        datman.add_sample_to_menu(self, new_item.filename, self.item_rows[old_filename].color_picker.color)
        datman.delete("None", self, old_filename)
    self.datadict[new_item.filename] = new_item
    plotting_tools.refresh_plot(self)

@Gtk.Template(resource_path="/se/sjoerd/DatMan/plot_settings.ui")
class PlotSettingsWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PlotSettingsWindow"
    datalist_chooser = Gtk.Template.Child()
    apply_button = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    linestyle_selected = Gtk.Template.Child()
    linestyle_unselected = Gtk.Template.Child()
    selected_line_thickness_slider = Gtk.Template.Child()
    unselected_line_thickness_slider = Gtk.Template.Child()
    selected_markers_chooser = Gtk.Template.Child()
    unselected_markers_chooser = Gtk.Template.Child()
    selected_marker_size = Gtk.Template.Child()
    unselected_marker_size = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.props.modal = True
        self.select_item = False
        data_list = utilities.get_datalist(parent)
        utilities.populate_chooser(self.datalist_chooser, data_list)
        self.set_transient_for=(parent.props.active_window)
        self.item = self.load_config(parent)
        self.datalist_chooser.connect("notify", self.on_notify, parent)
        self.connect("close-request", self.on_close, parent)
        style_context = self.apply_button.get_style_context()
        style_context.add_class("suggested-action")


    def on_notify(self, _, __, parent):
        filename = self.datalist_chooser.get_selected_item().get_string()
        self.load_config(parent, filename = filename)


    def load_config(self, parent, filename = None):
        data_list = utilities.get_datalist(parent)
        if filename is None:
            filename = self.datalist_chooser.get_selected_item().get_string()
        utilities.set_chooser(self.datalist_chooser, filename)
        item = parent.datadict[filename]
        self.selected_line_thickness_slider.set_range(0.1, 10)
        self.unselected_line_thickness_slider.set_range(0.1, 10)
        self.selected_marker_size.set_range(0, 30)
        self.unselected_marker_size.set_range(0, 30)
        utilities.set_chooser(self.linestyle_selected, item.linestyle_selected)
        utilities.set_chooser(self.linestyle_unselected, item.linestyle_unselected)
        self.selected_line_thickness_slider.set_value(item.selected_line_thickness)
        self.unselected_line_thickness_slider.set_value(item.unselected_line_thickness)
        self.selected_marker_size.set_value(item.selected_marker_size)
        self.unselected_marker_size.set_value(item.unselected_marker_size)
        utilities.populate_chooser(self.selected_markers_chooser, list(Line2D.markers.values()))
        self.selected_markers_chooser.get_model().append("none")
        utilities.populate_chooser(self.unselected_markers_chooser, list(Line2D.markers.values()))
        self.unselected_markers_chooser.get_model().append("none")
        utilities.set_chooser(self.selected_markers_chooser, item.selected_markers)
        utilities.set_chooser(self.unselected_markers_chooser, item.unselected_markers)
        self.item = item
        return item

    def set_config(self, item):
        old_filename = self.datalist_chooser.get_selected_item().get_string()
        if self.name_entry.get_text() != "":
            item.filename = self.name_entry.get_text()
        item.linestyle_selected = self.linestyle_selected.get_selected_item().get_string()
        item.linestyle_unselected = self.linestyle_unselected.get_selected_item().get_string()
        item.selected_markers = self.selected_markers_chooser.get_selected_item().get_string()
        item.unselected_markers = self.unselected_markers_chooser.get_selected_item().get_string()
        item.selected_line_thickness = self.selected_line_thickness_slider.get_value()
        item.unselected_line_thickness = self.unselected_line_thickness_slider.get_value()
        item.selected_marker_size = self.selected_marker_size.get_value()
        item.unselected_marker_size = self.unselected_marker_size.get_value()
        marker_dict = Line2D.markers
        item.selected_markers = utilities.get_dict_by_value(marker_dict, self.selected_markers_chooser.get_selected_item().get_string())
        item.unselected_markers = utilities.get_dict_by_value(marker_dict, self.unselected_markers_chooser.get_selected_item().get_string())
        return item, old_filename

    def on_close(self, _, parent):
        item = self.item
        new_item, old_filename = self.set_config(item)
        if old_filename != new_item.filename:
            datman.add_sample_to_menu(parent, new_item.filename, parent.item_rows[old_filename].color_picker.color)
            datman.delete("None", parent, old_filename)
        parent.datadict[new_item.filename] = new_item
        plotting_tools.refresh_plot(parent)
