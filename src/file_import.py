# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _
from pathlib import Path

from graphs import file_io, graphs


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
    def __init__(self, parent, file, name="", mode=None):
        self.file = file
        self.name = name
        self.mode = mode

        filename = file.query_info("standard::*", 0, None).get_display_name()

        if self.mode is None:
            try:
                file_suffix = Path(filename).suffixes[-1]
            except IndexError:
                file_suffix = None
            match file_suffix:
                case ".xrdml":
                    self.mode = "xrdml"
                case ".xry":
                    self.mode = "xry"
                case _:
                    self.mode = "columns"

        if not self.name:
            self.name = filename

        try:
            self.params = parent.preferences.import_params[self.mode]
        except KeyError:
            self.params = []
