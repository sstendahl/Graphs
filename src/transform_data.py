# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, Gtk

from graphs import operations


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/transform_window.ui")
class TransformWindow(Adw.Window):
    __gtype_name__ = "GraphsTransformWindow"
    transform_x_entry = Gtk.Template.Child()
    transform_y_entry = Gtk.Template.Child()
    discard = Gtk.Template.Child()
    help_button = Gtk.Template.Child()
    help_popover = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(application=application,
                         transient_for=application.get_window())
        self.transform_x_entry.set_text("X")
        self.transform_y_entry.set_text("Y")
        self.discard.set_visible(self.get_application().get_mode() == 1)
        self.present()
        self.help_button.connect(
            "clicked", lambda _x: self.help_popover.popup())

    @Gtk.Template.Callback()
    def on_accept(self, _widget):
        try:
            input_x = str(self.transform_x_entry.get_text())
            input_y = str(self.transform_y_entry.get_text())
            discard = self.discard.get_active()
            operations.perform_operation(
                self.get_application(), operations.transform,
                input_x, input_y, discard)
        except (RuntimeError, KeyError) as exception:
            toast = _("{name}: Unable to do transformation, \
make sure the syntax is correct").format(name=exception.__class__.__name__)
            self.get_application().get_window().add_toast_string(toast)
            logging.exception(_("Unable to do transformation"))
        self.destroy()
