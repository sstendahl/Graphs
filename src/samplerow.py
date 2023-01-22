import gi
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, Adw, GObject
from . import datman
from . import plotting_tools
@Gtk.Template(resource_path='/se/sjoerd/DatMan/sample_box.ui')
class SampleBox(Gtk.Box):
    __gtype_name__ = "SampleBox"
    delete_button = Gtk.Template.Child()
    sample_box = Gtk.Template.Child()
    sample_ID_label = Gtk.Template.Child()

    def __init__(self, app, filename = "", id = ""):
        super().__init__()
        self.filename = filename
        self.id = id
        self.app = app
        self.css = self.get_css()
        self.selected = False
        self.gesture = Gtk.GestureClick()
        self.add_controller(self.gesture)

    def rgba_to_tuple(rgba):
        return (rgba.red, rgba.green, rgba.blue, rgba.alpha)

    def clicked(self,gesture,_ ,xpos, ypos, datman):
        self.css = self.get_css()
        if not self.selected:
            self.selected = True
            datman.datadict[self.id].selected = True
            self.set_css_classes(['label_selected'])
        else:
            self.selected = False
            datman.datadict[self.id].selected = False
            self.set_css_classes(['label_deselected'])
        plotting_tools.refresh_plot(datman, set_limits = False)
        self.set_css(self.css)

    def get_css(self):
        if Adw.StyleManager.get_default().get_dark():
            css = '''
                 .label_deselected {
                     background-color: #242424;
                     color: white;
                 }
                .label_selected {
                    background-color: #3A3A3A;
                    color: white;
                }
                '''
        else:
            css = '''
                 .label_deselected {
                     background-color: #FAFAFA;
                     color: black;
                 }
                .label_selected {
                    background-color: #E6E6E6;
                    color: black;
                }
                '''
        return css


    def set_css(self, css):
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(css.encode())
            context = self.get_style_context()
            display = self.get_display()
            context.add_provider_for_display(display, css_provider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


