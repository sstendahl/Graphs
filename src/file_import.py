# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, Gtk

from graphs import file_io, graphs, misc, utilities


IMPORT_MODES = ["xrdml", "xry", "columns"]


def prepare_import(self, files, advanced):
    import_dict = {mode: [] for mode in IMPORT_MODES}
    for file in files:
        import_dict[guess_import_mode(file)].append(file)
    if advanced:
        modes = []
        for mode, files in import_dict.items():
            if files:
                modes.append(mode)
        if modes:
            ImportWindow(self, modes, import_dict)
            return
    prepare_import_finish(self, import_dict)


def prepare_import_finish(self, import_dict):
    import_settings_list = []
    for mode, files in import_dict.items():
        try:
            params = self.preferences.import_params[mode]
        except KeyError:
            params = []
        for file in files:
            import_settings_list.append(ImportSettings(file, mode, params))
    import_from_files(self, import_settings_list)


def import_from_files(self, import_settings_list):
    items = []
    for import_settings in import_settings_list:
        try:
            items.extend(_import_from_file(self, import_settings))
        except IndexError:
            message = \
                _("Could not open data, the column index is out of range")
            self.main_window.add_toast(message)
            logging.exception(message)
            continue
        except UnicodeDecodeError:
            message = _("Could not open data, wrong filetype")
            self.main_window.add_toast(message)
            logging.exception(message)
            continue
        except ValueError as error:
            message = error.message
            self.main_window.add_toast(message)
            logging.exception(message)
            continue
    graphs.add_items(self, items)


def _import_from_file(self, import_settings):
    match import_settings.mode:
        case "xrdml":
            callback = file_io.import_from_xrdml
        case "xry":
            callback = file_io.import_from_xry
        case "columns":
            callback = file_io.import_from_columns
    return callback(self, import_settings)


class ImportSettings():
    def __init__(self, file, mode, params):
        self.file = file
        self.mode = mode
        self.params = params
        self.name = file.query_info("standard::*", 0, None).get_display_name()


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/import.ui")
class ImportWindow(Adw.Window):
    __gtype_name__ = "ImportWindow"
    confirm_button = Gtk.Template.Child()
    columns_group = Gtk.Template.Child()

    delimiter = Gtk.Template.Child()
    separator = Gtk.Template.Child()
    column_x = Gtk.Template.Child()
    column_y = Gtk.Template.Child()
    skip_rows = Gtk.Template.Child()

    def __init__(self, parent, modes, import_dict):
        super().__init__()
        self.parent = parent
        self.modes = modes
        self.import_dict = import_dict
        self.import_params = parent.preferences.import_params
        visible = False
        if "columns" in self.modes:
            self.load_columns()
            visible = True
        if not visible:
            prepare_import_finish(self.parent, self.import_dict)
            self.destroy()
            return
        self.confirm_button.connect("clicked", self.on_accept)
        self.set_transient_for(parent.main_window)
        self.connect("close-request", self.on_close)
        self.present()

    def load_columns(self):
        params = self.import_params["columns"]
        self.columns_group.set_visible(True)
        self.delimiter.set_text(params["delimiter"])
        utilities.populate_chooser(self.separator, misc.SEPARATORS, False)
        utilities.set_chooser(self.separator, params["separator"])
        self.column_x.set_value(int(params["column_x"]))
        self.column_y.set_value(int(params["column_y"]))
        self.skip_rows.set_value(int(params["skip_rows"]))

    def on_accept(self, _widget):
        self.param_dict = {}
        if "columns" in self.modes:
            self.load_columns()
        import_settings_list = []
        for mode in IMPORT_MODES:
            try:
                params = self.param_dict[mode]
            except KeyError:
                try:
                    params = self.import_params[mode]
                except KeyError:
                    params = []
            for file in self.import_dict[mode]:
                import_settings_list.append(ImportSettings(file, mode, params))
        import_from_files(self.parent, import_settings_list)
        self.destroy()

    def get_columns(self):
        self.param_dict["columns"] = {
            "column_x": int(self.column_x.get_value()),
            "column_y": int(self.column_y.get_value()),
            "skip_rows": int(self.skip_rows.get_value()),
            "separator": utilities.get_selected_chooser_item(self.separator),
            "delimiter": self.delimiter.get_text(),
        }

    def on_close(self, _widget):
        prepare_import_finish(self.parent, self.import_dict)


def guess_import_mode(file):
    try:
        filename = file.query_info("standard::*", 0, None).get_display_name()
        file_suffix = Path(filename).suffixes[-1]
    except IndexError:
        file_suffix = None
    match file_suffix:
        case ".xrdml":
            return "xrdml"
        case ".xry":
            return "xry"
        case _:
            return "columns"
