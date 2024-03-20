# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, GObject, Graphs, Gtk

from graphs import operations


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/transform.ui")
class TransformDialog(Adw.Dialog):
    __gtype_name__ = "GraphsTransformDialog"
    transform_x_entry = Gtk.Template.Child()
    transform_y_entry = Gtk.Template.Child()
    discard = Gtk.Template.Child()
    help_button = Gtk.Template.Child()
    help_popover = Gtk.Template.Child()

    application = GObject.Property(type=Graphs.Application)

    def __init__(self, application):
        super().__init__(application=application)
        self.transform_x_entry.set_text("X")
        self.transform_y_entry.set_text("Y")
        self.discard.set_visible(application.get_mode() == 2)
        self.present(application.get_window())
        self.help_button.connect(
            "clicked", lambda _x: self.help_popover.popup())

    @Gtk.Template.Callback()
    def on_accept(self, _widget) -> None:
        try:
            input_x = str(self.transform_x_entry.get_text())
            input_y = str(self.transform_y_entry.get_text())
            discard = self.discard.get_active()
            operations.perform_operation(
                self.props.application, operations.transform,
                input_x, input_y, discard)
        except (RuntimeError, KeyError) as exception:
            toast = _("{name}: Unable to do transformation, \
make sure the syntax is correct").format(name=exception.__class__.__name__)
            self.props.application.get_window().add_toast_string(toast)
            logging.exception(_("Unable to do transformation"))
        self.close()
