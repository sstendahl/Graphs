# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from gettext import gettext as _
from pathlib import Path

from graphs import clipboard, file_io, graphs, ui
from graphs.misc import ImportSettings


def import_from_files(self, files, import_settings=None):
    if import_settings is None:
        import_settings = ImportSettings(self.preferences.config)
    for file in files:
        try:
            item = _import_from_file(self, file, import_settings)
            if not item.xdata:
                filename = \
                    file.query_info("standard::*", 0, None).get_display_name()
                raise ValueError(
                    _("Unable to retrieve data for {}".format(filename)))
            graphs.add_item(self, item)
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
    clipboard.add(self)
    ui.reload_item_menu(self)
    graphs.reload(self)


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
    item = callback(self, file, import_settings)
    item.name = import_settings.name
    if not item.name:
        item.name = filename
    return item
