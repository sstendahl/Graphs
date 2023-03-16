# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from gi.repository import Adw, Gtk

from graphs import operations
from graphs.misc import InteractionMode


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/transform_window.ui")
class TransformWindow(Adw.Window):
    __gtype_name__ = "TransformWindow"
    transform_x_entry = Gtk.Template.Child()
    transform_y_entry = Gtk.Template.Child()
    confirm_button = Gtk.Template.Child()
    discard_row = Gtk.Template.Child()
    discard = Gtk.Template.Child()
    help_button = Gtk.Template.Child()
    help_popover = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.transform_x_entry.set_text("X")
        self.transform_y_entry.set_text("Y")
        self.discard_row.set_visible(
            parent.interaction_mode == InteractionMode.SELECT)
        self.confirm_button.connect("clicked", self.accept, parent)
        self.set_transient_for(parent.main_window)
        self.present()
        self.help_button.connect("clicked",
            lambda x: self.help_popover.popup())

    def accept(self, _widget, parent):
        try:
            input_x = str(self.transform_x_entry.get_text())
            input_y = str(self.transform_y_entry.get_text())
            discard = self.discard.get_active()
            operations.operation(
                parent, operations.transform, input_x, input_y, discard)
        except Exception as exception:
            exception_type = exception.__class__.__name__
            toast = f"{exception_type}: Unable to do transformation, \
make sure the syntax is correct"
            parent.main_window.add_toast(toast)
            logging.exception("Unable to do transformation")
        self.destroy()
