# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gtk, Adw

from . import plotting_tools

def open_rename_label_window(self, axis):
    win = RenameLabelWindow(self, axis)
    win.set_transient_for(self.main_window)
    win.set_modal(True)
    button = win.rename_label_confirm_button
    button.connect("clicked", on_accept, self, win, axis)
    win.present()

def on_accept(widget, self, window, axis):
    window.rename(self, axis)
    plotting_tools.reload_plot(self)
    window.destroy()

@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/rename_label_window.ui")
class RenameLabelWindow(Adw.Window):
    __gtype_name__ = "RenameLabelWindow"
    rename_label_confirm_button = Gtk.Template.Child()
    label_entry = Gtk.Template.Child()
    preferencegroup = Gtk.Template.Child()

    def __init__(self, parent, axis):
        super().__init__()
        style_context = self.rename_label_confirm_button.get_style_context()
        style_context.add_class("suggested-action")
        if axis == parent.canvas.title:
            self.set_title("Rename Title")
            self.preferencegroup.set_title("Change Title")
            self.preferencegroup.set_description("Here you can change the title of the plot")
            self.label_entry.set_title("Title")
        self.load_settings(parent, axis)
    
    def load_settings(self, parent, axis):
        self.label_entry.set_text(axis.get_text())
        
    def rename(self, parent, axis):
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
