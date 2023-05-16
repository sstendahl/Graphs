# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _
from pathlib import Path

from graphs import file_io, graphs
from graphs.misc import ImportSettings


def import_from_files(self, files, import_settings=None):
    if import_settings is None:
        import_settings = ImportSettings(self.preferences.config)
    items = []
    for file in files:
        try:
            items.extend(_import_from_file(self, file, import_settings))
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


def _import_from_file(self, file, import_settings):
    filename = file.query_info("standard::*", 0, None).get_display_name()
    try:
        file_suffix = Path(filename).suffixes[-1]
    except IndexError:
        file_suffix = None
    match file_suffix:
        case ".xrdml":
            callback = file_io.import_from_xrdml
        case ".xry":
            callback = file_io.import_from_xry
        case _:
            callback = file_io.import_from_columns
    items = callback(self, file, import_settings)
    if not import_settings.name:
        i = 0
        for item in items:
            if i < 1:
                item.name = filename
            else:
                item.name = f"{filename} ({i})"
    return items
