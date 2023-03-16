# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

from graphs import graphs


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/rename_label_window.ui")
class RenameLabelWindow(Adw.Window):
    __gtype_name__ = "RenameLabelWindow"
    confirm_button = Gtk.Template.Child()
    label_entry = Gtk.Template.Child()
    preferencegroup = Gtk.Template.Child()

    def __init__(self, parent, axis):
        super().__init__()
        if axis == parent.canvas.title:
            self.set_title("Rename Title")
            self.preferencegroup.set_title("Change Title")
            self.preferencegroup.set_description(
                "Here you can change the title of the plot")
            self.label_entry.set_title("Title")
        self.label_entry.set_text(axis.get_text())
        self.set_transient_for(parent.main_window)
        self.confirm_button.connect("clicked", self.accept, parent, axis)
        self.present()

    def accept(self, _widget, parent, axis):
        if axis == parent.canvas.top_label:
            parent.plot_settings.top_label = self.label_entry.get_text()
        if axis == parent.canvas.left_label:
            parent.plot_settings.ylabel = self.label_entry.get_text()
        if axis == parent.canvas.bottom_label:
            parent.plot_settings.xlabel = self.label_entry.get_text()
        if axis == parent.canvas.right_label:
            parent.plot_settings.right_label = self.label_entry.get_text()
        if axis == parent.canvas.title:
            parent.plot_settings.title = self.label_entry.get_text()
        graphs.reload(parent)
        self.destroy()
