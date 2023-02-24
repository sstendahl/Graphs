# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gtk

from graphs import plotting_tools, utilities

from matplotlib import colors


class ColorPicker():
    def __init__(self, color, key, parent, button):
        super().__init__()
        self.parent = parent
        self.key = key
        self.button = button
        self.color = color

        press_gesture = Gtk.GestureClick()
        press_gesture.connect("pressed", self.change_color)
        self.color_chooser = Gtk.ColorChooserWidget.new()
        self.color_chooser.set_use_alpha(False)
        self.color_chooser.show()
        self.color_chooser.connect("color-activated", self.change_color)
        self.color_chooser.add_controller(press_gesture)

        self.color_popover = Gtk.Popover()
        self.color_popover.set_parent(self.button)
        self.color_popover.set_child(self.color_chooser)
        self.color_popover.connect("closed", self.change_color)
        self.button.connect("clicked", self.on_click)
        self.set_css()
        self.color = self.get_color()
        parent.datadict[self.key].color = self.color

    def set_rgba(self, color):
        self.color_chooser.set_rgba(color)
        self.update_color()

    def on_click(self, _button):
        self.popover_active = True
        self.color_chooser.props.show_editor = False
        self.color_popover.popup()

    def set_color(self, color):
        self.set_rgba(color)
        self.color = self.get_color()
        self.update_color()
        self.parent.datadict[self.key].color = self.color
        plotting_tools.refresh_plot(self.parent)

    def change_color(self, *_args):
        self.set_color(self.get_rgba())

    def get_rgba(self):
        return self.color_chooser.get_rgba()

    def get_color(self):
        color_rgba = self.get_rgba()
        return utilities.rgba_to_hex(color_rgba)

    def update_color(self):
        css = f"button {{ color: {self.get_rgba().to_string()}; }}"
        self.provider.load_from_data(css.encode())

    def set_css(self):
        self.provider = Gtk.CssProvider()
        context = self.button.get_style_context()
        context.add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        rgba = utilities.create_rgba(*colors.to_rgba(self.color))
        self.set_rgba(rgba)
        self.set_rgba(self.get_rgba())
        self.update_color()
