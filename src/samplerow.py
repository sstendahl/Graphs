# SPDX-License-Identifier: GPL-3.0-or-later
import time

from gi.repository import Gtk

from graphs import colorpicker, graphs, plotting_tools, ui, utilities
from graphs.plot_settings import PlotSettingsWindow


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/sample_box.ui")
class SampleBox(Gtk.Box):
    __gtype_name__ = "SampleBox"
    sample_box = Gtk.Template.Child()
    sample_id_label = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()

    def __init__(self, parent, key, color, label, selected=False):
        super().__init__()
        max_length = int(26)
        if len(label) > max_length:
            label = f"{label[:max_length]}..."
        if selected:
            self.check_button.set_active(True)
        self.sample_id_label.set_text(label)
        self.key = key
        self.parent = parent
        self.one_click_trigger = False
        self.time_first_click = 0
        self.gesture = Gtk.GestureClick()
        self.gesture.set_button(0)
        self.add_controller(self.gesture)
        self.gesture.connect("released", self.clicked, parent)
        self.delete_button.connect("clicked", self.delete)
        self.color_picker = colorpicker.ColorPicker(color, key, parent)
        self.sample_box.insert_child_after(self.color_picker, self.sample_id_label)
        self.check_button.connect("toggled", self.toggled)

    def delete(self, _):
        graphs.delete(self.parent, self.key, True)

    def toggled(self, _):
        plotting_tools.refresh_plot(self.parent)
        ui.enable_data_dependent_buttons(self.parent, utilities.get_selected_keys(self.parent))

    def clicked(self, _gesture, _, _xpos, _ypos, graph):
        if not self.one_click_trigger:
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
                win = PlotSettingsWindow(self.parent, self.key)
                win.present()
