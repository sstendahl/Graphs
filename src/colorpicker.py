import gi
from . import plotting_tools, datman
from gi.repository import Gtk, GObject, Gdk
from matplotlib import colors

class ColorPicker(Gtk.ColorButton):

    def __init__(self, color):
        super().__init__()
        self.set_tooltip_text(_("Pick a color"))
        self.provider = Gtk.CssProvider()
        rgba = datman.create_rgba(*colors.to_rgba(color))
        self.set_rgba(rgba)
        self.color = color
        self.update_color()

    def on_color_set(self, widget, datman):
        self.color = self.get_color()
        self.update_color()
        plotting_tools.refresh_plot(datman)

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
            display = self.get_display()
            self.provider.load_from_data(css.encode())
            context.add_provider_for_display(display, css_provider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_USER)
