# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _

from gi.repository import Adw, GLib, Gtk

from graphs import operations
from graphs.misc import InteractionMode
from graphs.transform_data import TransformWindow


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/window.ui")
class GraphsWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GraphsWindow"
    undo_button = Gtk.Template.Child()
    redo_button = Gtk.Template.Child()
    view_back_button = Gtk.Template.Child()
    view_forward_button = Gtk.Template.Child()
    item_list = Gtk.Template.Child()
    sidebar_flap = Gtk.Template.Child()
    pan_button = Gtk.Template.Child()
    zoom_button = Gtk.Template.Child()
    select_button = Gtk.Template.Child()
    shift_vertically_button = Gtk.Template.Child()
    cut_button = Gtk.Template.Child()
    translate_x_entry = Gtk.Template.Child()
    translate_y_entry = Gtk.Template.Child()
    multiply_x_entry = Gtk.Template.Child()
    multiply_y_entry = Gtk.Template.Child()
    top_scale = Gtk.Template.Child()
    left_scale = Gtk.Template.Child()
    bottom_scale = Gtk.Template.Child()
    right_scale = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def add_toast(self, title):
        self.toast_overlay.add_toast(Adw.Toast(title=title))

    @Gtk.Template.Callback()
    def on_sidebar_toggle(self, *_args):
        self.get_application().toggle_sidebar.change_state(
            GLib.Variant.new_boolean(self.sidebar_flap.get_reveal_flap()))

    @Gtk.Template.Callback()
    def shift_vertically(self, *_args):
        app = self.props.application
        operations.perform_operation(
            app, operations.shift_vertically,
            app.plot_settings.yscale, app.plot_settings.right_scale,
            app.datadict)

    @Gtk.Template.Callback()
    def normalize(self, *_args):
        operations.perform_operation(
            self.props.application, operations.normalize)

    @Gtk.Template.Callback()
    def smoothen(self, *_args):
        operations.perform_operation(
            self.props.application, operations.smoothen)

    @Gtk.Template.Callback()
    def center(self, *_args):
        operations.perform_operation(
            self.props.application, operations.center,
            self.props.application.preferences["action_center_data"])

    @Gtk.Template.Callback()
    def combine(self, *_args):
        operations.combine(self.props.application)

    @Gtk.Template.Callback()
    def cut(self, *_args):
        if self.props.application.interaction_mode == InteractionMode.SELECT:
            operations.perform_operation(
                self.props.application, operations.cut_selected)

    @Gtk.Template.Callback()
    def translate_x(self, *_args):
        try:
            offset = eval(self.translate_x_entry.get_text())
        except ValueError as exception:
            message = _("{error}: Unable to do translation, \
make sure to enter a valid number").format(error=exception.__class__.__name__)
            self.add_toast(message)
            logging.exception(message)
            offset = 0
        operations.perform_operation(
            self.props.application, operations.translate_x, offset)

    @Gtk.Template.Callback()
    def translate_y(self, *_args):
        try:
            offset = eval(self.translate_y_entry.get_text())
        except ValueError as exception:
            message = _("{error}: Unable to do translation, \
make sure to enter a valid number").format(error=exception.__class__.__name__)
            self.add_toast(message)
            logging.exception(message)
            offset = 0
        operations.perform_operation(
            self.props.application, operations.translate_y, offset)

    @Gtk.Template.Callback()
    def multiply_x(self, *_args):
        try:
            multiplier = eval(self.multiply_x_entry.get_text())
        except ValueError as exception:
            message = _("{error}: Unable to do translation, \
make sure to enter a valid number").format(error=exception.__class__.__name__)
            self.add_toast(message)
            logging.exception(message)
            multiplier = 1
        operations.perform_operation(
            self.props.application, operations.multiply_x, multiplier)

    @Gtk.Template.Callback()
    def multiply_y(self, *_args):
        try:
            multiplier = eval(self.multiply_y_entry.get_text())
        except ValueError as exception:
            message = _("{error}: Unable to do translation, \
make sure to enter a valid number").format(error=exception.__class__.__name__)
            self.add_toast(message)
            logging.exception(message)
            multiplier = 1
        operations.perform_operation(
            self.props.application, operations.multiply_y, multiplier)

    @Gtk.Template.Callback()
    def derivative(self, *_args):
        operations.perform_operation(
            self.props.application, operations.get_derivative)

    @Gtk.Template.Callback()
    def integral(self, *_args):
        operations.perform_operation(
            self.props.application, operations.get_integral)

    @Gtk.Template.Callback()
    def fourier(self, *_args):
        operations.perform_operation(
            self.props.application, operations.get_fourier)

    @Gtk.Template.Callback()
    def inverse_fourier(self, *_args):
        operations.perform_operation(
            self.props.application, operations.get_inverse_fourier)

    @Gtk.Template.Callback()
    def transform(self, *_args):
        TransformWindow(self.props.application)
