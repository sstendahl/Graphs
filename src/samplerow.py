# SPDX-License-Identifier: GPL-3.0-or-later
import gi
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, Adw, GObject
from . import graphs
from . import plotting_tools
@Gtk.Template(resource_path='/se/sjoerd/Graphs/ui/sample_box.ui')
class SampleBox(Gtk.Box):
    __gtype_name__ = "SampleBox"
    sample_box = Gtk.Template.Child()
    sample_ID_label = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()
    
    def __init__(self, app, filename = "", id = ""):
        super().__init__()
        self.filename = filename
        self.sample_ID_label.set_text(filename)
        self.id = id
        self.app = app
        self.selected = False
        self.gesture = Gtk.GestureClick()
        self.add_controller(self.gesture)

    def rgba_to_tuple(rgba):
        return (rgba.red, rgba.green, rgba.blue, rgba.alpha)

    def clicked(self,gesture,_ ,xpos, ypos, graphs):
        pass
