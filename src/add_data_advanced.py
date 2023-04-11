# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

from graphs import ui, utilities
from graphs.misc import ImportSettings


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/add_data_advanced.ui")
class AddAdvancedWindow(Adw.Window):
    __gtype_name__ = "AddAdvancedWindow"
    name = Gtk.Template.Child()
    delimiter = Gtk.Template.Child()
    separator = Gtk.Template.Child()
    column_x = Gtk.Template.Child()
    column_y = Gtk.Template.Child()
    skip_rows = Gtk.Template.Child()
    guess_headers = Gtk.Template.Child()
    confirm_button = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        config = parent.preferences.config
        self.delimiter.set_text(config["import_delimiter"])
        utilities.set_chooser(self.separator, config["import_separator"])
        self.column_x.set_value(int(config["import_column_x"]))
        self.column_y.set_value(int(config["import_column_y"]))
        self.skip_rows.set_value(int(config["import_skip_rows"]))
        self.guess_headers.set_active(config["guess_headers"])
        self.confirm_button.connect("clicked", self.on_accept)
        self.set_transient_for(parent.main_window)
        self.present()

    def on_accept(self, _widget):
        """
        Runs when the dataset is loaded, uses the selected settings in the
        window to set the import settings during loading
        """
        params = {
            "column_x": int(self.column_x.get_value()),
            "column_y": int(self.column_y.get_value()),
            "skip_rows": int(self.skip_rows.get_value()),
            "separator": self.separator.get_selected_item().get_string(),
            "delimiter": self.delimiter.get_text(),
            "guess_headers": self.guess_headers.get_active(),
        }
        name = self.name.get_text()
        config = self.parent.preferences.config
        dialog = Gtk.FileDialog()
        dialog.open_multiple(
            self.parent.main_window, None, ui.on_add_data_response,
            self.parent, ImportSettings(config, params=params, name=name))
        self.destroy()
