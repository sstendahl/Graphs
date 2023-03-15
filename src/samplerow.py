# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gtk

from graphs import colorpicker, graphs, ui, utilities
from graphs.edit_item import EditItemWindow


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/sample_box.ui")
class SampleBox(Gtk.Box):
    __gtype_name__ = "SampleBox"
    sample_box = Gtk.Template.Child()
    label = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()
    color_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()

    def __init__(self, parent, key, color, label, selected=False):
        super().__init__()
        self.label.set_text(utilities.shorten_label(label))
        if selected:
            self.check_button.set_active(True)
        self.key = key
        self.parent = parent
        self.one_click_trigger = False
        self.time_first_click = 0
        self.gesture = Gtk.GestureClick()
        self.gesture.set_button(0)
        self.add_controller(self.gesture)
        self.edit_button.connect("clicked", self.edit)
        self.delete_button.connect("clicked", self.delete)
        self.color_picker = colorpicker.ColorPicker(color, key, parent,
                                                    self.color_button)
        self.check_button.connect("toggled", self.toggled)

    def delete(self, _):
        graphs.delete_item(self.parent, self.key, True)

    def toggled(self, _):
        graphs.refresh(self.parent, False)
        ui.enable_data_dependent_buttons(
            self.parent, utilities.get_selected_keys(self.parent))

    def edit(self, _):
        EditItemWindow(self.parent, self.parent.datadict[self.key])
