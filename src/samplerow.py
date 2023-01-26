import gi
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, Adw, GObject
from . import datman
from . import plotting_tools
@Gtk.Template(resource_path='/se/sjoerd/DatMan/sample_box.ui')
class SampleBox(Gtk.Box):
    __gtype_name__ = "SampleBox"
    sample_box = Gtk.Template.Child()
    sample_ID_label = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    check_mark = Gtk.Template.Child()
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

    def clicked(self,gesture,_ ,xpos, ypos, datman):
        win = datman.props.active_window
        list_box = win.list_box
        if not self.selected:
            self.selected = True
            print(f"Selecting key {self.id}")
            print(datman.sample_menu[self.id])
            list_box.select_row(datman.sample_menu[self.id])
            datman.datadict[self.id].selected = True
        else:
            self.selected = False
            print(f"Unselecting key {self.id}")
            datman.datadict[self.id].selected = False
            list_box.unselect_row(datman.sample_menu[self.id])
        plotting_tools.refresh_plot(datman, set_limits = False)
