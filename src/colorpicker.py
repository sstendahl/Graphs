# SPDX-License-Identifier: GPL-3.0-or-later
import gi
from . import plotting_tools, utilities
from gi.repository import Gtk, GObject, Gdk
from matplotlib import colors

class ColorPicker(Gtk.ColorButton):
    def __init__(self, color, row, parent):
        super().__init__()
        self.set_tooltip_text(_("Pick a color"))
        self.provider = Gtk.CssProvider()
        self.set_size_request(10, 15)
        rgba = utilities.create_rgba(*colors.to_rgba(color))
        self.set_rgba(rgba)
        self.connect("color-set", self.on_color_set, parent)
        style_context = self.get_style_context()        
        style_context.add_class("circular")                
        self.color = color
        self.update_color()

    def on_color_set(self, widget, graphs):
        self.color = self.get_color()
        self.update_color()
        plotting_tools.refresh_plot(graphs)

    def convert_rgba(self, rgba):
        return (round(rgba.red*255), round(rgba.green*255), round(rgba.blue*255), round(rgba.alpha*255))

    def get_color(self):
        color_rgba = self.convert_rgba(self.get_rgba())
        color_hex = '#{:02x}{:02x}{:02x}'.format(*color_rgba)
        return color_hex

    def update_color(self):
        color = self.get_color()
        self.set_css_classes([f"button_{color[1:]}", "flat"])
        css = f'''
                 .button_{color[1:]} {{
                      color: {color};
                 }}
                '''
        self.set_css(css)


    def set_css(self, css):
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(css.encode())
            context = self.get_style_context()
            context.add_class("circular")    
            display = self.get_display()
            self.provider.load_from_data(css.encode())
            context.add_provider_for_display(display, css_provider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_USER)
