# SPDX-License-Identifier: GPL-3.0-or-later
import gi
from . import plotting_tools, utilities
from gi.repository import Gtk, GObject, Gdk
from matplotlib import colors

class ColorPicker(Gtk.Button):
    def __init__(self, color, row, parent):
        super().__init__()
        #self.set_size_request(45, -1)
        self.row = row
        self.parent = parent
        self.set_tooltip_text(_("Pick a color"))
        self.color = color
        style_context = self.get_style_context()
        style_context.add_class("circular")

        press_gesture = Gtk.GestureClick()
        press_gesture.connect("pressed", self.change_color)
        
        self.color_chooser = Gtk.ColorChooserWidget.new()
        self.color_chooser.set_use_alpha(False)
        self.color_chooser.show()
        self.color_chooser.connect("color-activated", self.change_color)        
        self.color_chooser.add_controller(press_gesture)

        self.color_popover = Gtk.Popover()
        self.color_popover.set_parent(self)
        self.color_popover.set_child(self.color_chooser)
        self.color_popover.connect("closed", self.change_color)
        self.connect("clicked", self.on_click)
        self.set_css()

    def on_color_set(self, widget, graphs):
        self.color = self.get_color()
        self.update_color()
        plotting_tools.refresh_plot(graphs)

    def set_rgba(self, color):
        self.color_chooser.set_rgba(color)
        self.update_color()

    def on_click(self, button):
        self.popover_active = True
        self.color_chooser.props.show_editor = False
        self.color_popover.popup()

    def set_color(self, chooser, color, _ = None):
        self.set_rgba(color)
        self.color = self.get_color()
        self.update_color()
        plotting_tools.refresh_plot(self.parent)

    def change_color(self, *args):
        self.set_color(self.color_chooser, self.get_rgba())

    def get_rgba(self):
        return self.color_chooser.get_rgba()

    def convert_rgba(self, rgba):
        return (round(rgba.red*255), round(rgba.green*255), round(rgba.blue*255), round(rgba.alpha*255))

    def get_color(self):
        color_rgba = self.convert_rgba(self.get_rgba())
        color_hex = '#{:02x}{:02x}{:02x}'.format(*color_rgba)
        return color_hex

    def update_color(self):
        css = f'button {{ background: {self.get_rgba().to_string()}; }}'
        self.provider.load_from_data(css.encode())

    def set_css(self):
        self.provider = Gtk.CssProvider()
        context = self.get_style_context()
        context.add_provider(self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        rgba = utilities.create_rgba(*colors.to_rgba(self.color))
        self.set_rgba(rgba)
        self.set_rgba(self.get_rgba())
        self.update_color()
