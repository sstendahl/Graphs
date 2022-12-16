from gi.repository import Gtk, Adw, GObject, Gio
from numpy import *
from . import item_operations, plotting_tools, datman
from .data import Data

def open_add_data_advanced_window(widget, _, self):
    win = AddAdvancedWindow(self)
    win.present()


@Gtk.Template(resource_path="/se/sjoerd/DatMan/add_data_advanced.ui")
class AddAdvancedWindow(Adw.Window):
    __gtype_name__ = "AddAdvancedWindow"

    def __init__(self, parent):
        super().__init__()
        self.set_transient_for=(parent.props.active_window)
        self.props.modal = True
