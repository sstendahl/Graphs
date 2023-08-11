# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, GLib, Gtk

from graphs import operations, utilities
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
            app.plot_settings.left_scale, app.plot_settings.right_scale,
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
            self.props.application.settings.get_child(
                "general").get_enum("center"))

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
            offset = utilities.string_to_float(
                self.translate_x_entry.get_text())
            operations.perform_operation(
                self.props.application, operations.translate_x, offset)
        except ValueError as error:
            self.add_toast(error)

    @Gtk.Template.Callback()
    def translate_y(self, *_args):
        try:
            offset = utilities.string_to_float(
                self.translate_y_entry.get_text())
            operations.perform_operation(
                self.props.application, operations.translate_y, offset)
        except ValueError as error:
            self.add_toast(error)

    @Gtk.Template.Callback()
    def multiply_x(self, *_args):
        try:
            multiplier = utilities.string_to_float(
                self.multiply_x_entry.get_text())
            operations.perform_operation(
                self.props.application, operations.multiply_x, multiplier)
        except ValueError as error:
            self.add_toast(error)

    @Gtk.Template.Callback()
    def multiply_y(self, *_args):
        try:
            multiplier = utilities.string_to_float(
                self.multiply_y_entry.get_text())
            operations.perform_operation(
                self.props.application, operations.multiply_y, multiplier)
        except ValueError as error:
            self.add_toast(error)

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
