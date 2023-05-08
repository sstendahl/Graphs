# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

from graphs import clipboard, graphs, misc, ui, utilities


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/edit_item.ui")
class EditItemWindow(Adw.PreferencesWindow):
    __gtype_name__ = "EditItemWindow"
    item_selector = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    plot_x_position = Gtk.Template.Child()
    plot_y_position = Gtk.Template.Child()
    linestyle = Gtk.Template.Child()
    linewidth = Gtk.Template.Child()
    markers = Gtk.Template.Child()
    markersize = Gtk.Template.Child()

    def __init__(self, parent, item):
        super().__init__()
        self.parent = parent
        self.item = item
        names = utilities.get_all_names(self.parent)
        utilities.populate_chooser(self.item_selector, names)
        self.item_selector.set_selected(names.index(self.item.name))

        self.linewidth.set_range(0, 10)
        utilities.populate_chooser(self.plot_x_position, misc.X_POSITIONS)
        utilities.populate_chooser(self.plot_y_position, misc.Y_POSITIONS)
        utilities.populate_chooser(self.linestyle, misc.LINESTYLES)
        utilities.populate_chooser(self.markers, sorted(misc.MARKERS.keys()))
        self.markersize.set_range(0, 10)
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

        # If item_selector no longer matches with name, repopulate it
        names = utilities.get_all_names(self.parent)
        if set(names) != set(self.item_selector.untranslated_items):
            utilities.populate_chooser(self.item_selector, names, False)
            self.item_selector.set_selected(index)
            self.parent.datadict_clipboard = \
                self.parent.datadict_clipboard[:-1]

    def load_values(self):
        self.set_title(self.item.name)
        self.name_entry.set_text(self.item.name)
        utilities.set_chooser(
            self.plot_x_position, self.item.plot_x_position)
        utilities.set_chooser(
            self.plot_y_position, self.item.plot_y_position)
        utilities.set_chooser(self.linestyle, self.item.linestyle)
        self.linewidth.set_value(self.item.linewidth)
        markerstyle = utilities.get_dict_by_value(
            misc.MARKERS, self.item.markerstyle)
        utilities.set_chooser(self.markers, markerstyle)
        self.markersize.set_value(self.item.markersize)

    def apply(self, _):

        self.item.name = self.name_entry.get_text()

        # Only change limits when axes change, otherwise this is not needed
        set_limits = \
            self.item.plot_x_position \
            != utilities.get_selected_chooser_item(self.plot_x_position) \
            or self.item.plot_y_position \
            != utilities.get_selected_chooser_item(self.plot_y_position)

        self.item.plot_x_position = \
            utilities.get_selected_chooser_item(self.plot_x_position)
        self.item.plot_y_position = \
            utilities.get_selected_chooser_item(self.plot_y_position)
        self.item.linestyle = \
            utilities.get_selected_chooser_item(self.linestyle)
        self.item.linewidth = self.linewidth.get_value()
        self.item.markerstyle = \
            misc.MARKERS[utilities.get_selected_chooser_item(self.markers)]
        self.item.markersize = self.markersize.get_value()
        ui.reload_item_menu(self.parent)
        clipboard.add(self.parent)
        graphs.refresh(self.parent, set_limits)
