# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

from graphs import graphs, misc, plotting_tools, ui, utilities
from graphs.item import Item


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/edit_item.ui")
class EditItemWindow(Adw.PreferencesWindow):
    __gtype_name__ = "EditItemWindow"
    item_selector = Gtk.Template.Child()
    name = Gtk.Template.Child()
    xposition = Gtk.Template.Child()
    yposition = Gtk.Template.Child()

    item_group = Gtk.Template.Child()
    linestyle = Gtk.Template.Child()
    linewidth = Gtk.Template.Child()
    markerstyle = Gtk.Template.Child()
    markersize = Gtk.Template.Child()

    def __init__(self, application, item):
        super().__init__(application=application,
                         transient_for=application.main_window)
        self.item = item
        names = utilities.get_all_names(self.props.application)
        keys = list(self.props.application.datadict.keys())
        utilities.populate_chooser(self.xposition, misc.X_POSITIONS)
        utilities.populate_chooser(self.yposition, misc.Y_POSITIONS)
        utilities.populate_chooser(self.linestyle, misc.LINESTYLES)
        utilities.populate_chooser(
            self.markerstyle, sorted(misc.MARKERS.keys()))
        self.load_values()
        utilities.populate_chooser(self.item_selector, names)
        self.item_selector.set_selected(keys.index(item.key))
        self.present()

    @Gtk.Template.Callback()
    def on_close(self, *_args):
        self.apply()

    @Gtk.Template.Callback()
    def on_select(self, _action, _target):
        self.apply()
        data_list = list(self.props.application.datadict.keys())
        index = self.item_selector.get_selected()
        self.item = self.props.application.datadict[data_list[index]]
        self.load_values()

        # If item_selector no longer matches with name, repopulate it
        names = utilities.get_all_names(self.props.application)
        if set(names) != set(self.item_selector.untranslated_items):
            utilities.populate_chooser(self.item_selector, names, False)
            self.item_selector.set_selected(index)

    def load_values(self):
        self.set_title(self.item.name)
        self.name.set_text(self.item.name)
        utilities.set_chooser(self.xposition, self.item.xposition)
        utilities.set_chooser(self.yposition, self.item.yposition)
        self.item_group.set_visible(False)
        if isinstance(self.item, Item):
            self.load_item_values()

    def load_item_values(self):
        self.item_group.set_visible(True)
        utilities.set_chooser(self.linestyle, self.item.linestyle)
        self.linewidth.set_value(self.item.linewidth)
        markerstyle = utilities.get_dict_by_value(
            misc.MARKERS, self.item.markerstyle)
        utilities.set_chooser(self.markerstyle, markerstyle)
        self.markersize.set_value(self.item.markersize)

    def apply(self):
        self.item.name = self.name.get_text()

        # Only change limits when axes change, otherwise this is not needed
        set_limits = \
            self.item.xposition \
            != utilities.get_selected_chooser_item(self.xposition) \
            or self.item.yposition \
            != utilities.get_selected_chooser_item(self.yposition)

        self.item.xposition = \
            utilities.get_selected_chooser_item(self.xposition)
        self.item.yposition = \
            utilities.get_selected_chooser_item(self.yposition)
        if isinstance(self.item, Item):
            self.apply_item_values()
        ui.reload_item_menu(self.props.application)
        self.props.application.props.clipboard.add()
        graphs.refresh(self.props.application)
        if set_limits:
            plotting_tools.optimize_limits(self.props.application)

    def apply_item_values(self):
        self.item.linestyle = \
            utilities.get_selected_chooser_item(self.linestyle)
        self.item.linewidth = self.linewidth.get_value()
        self.item.markerstyle = \
            misc.MARKERS[utilities.get_selected_chooser_item(self.markerstyle)]
        self.item.markersize = self.markersize.get_value()
