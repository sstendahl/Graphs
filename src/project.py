# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gio

from graphs import file_io, item, migrate, ui


def save_project(self, file: Gio.File):
    figure_settings = self.get_data().get_figure_settings()
    figure_settings_dict = {
        key: figure_settings.get_property(key)
        for key in dir(figure_settings.props)
    }
    file_io.write_json(file, {
        "version": self.get_version(),
        "data": [item.to_dict(item_) for item_ in self.get_data()],
        "figure-settings": figure_settings_dict,
        "data-clipboard": self.get_clipboard().get_clipboard(),
        "data-clipboard-position": self.get_clipboard().get_clipboard_pos(),
        "view-clipboard": self.get_view_clipboard().get_clipboard(),
        "view-clipboard-position":
            self.get_view_clipboard().get_clipboard_pos(),
    }, False)


def load_project(self, file: Gio.File):
    try:
        project = file_io.parse_json(file)
    except UnicodeDecodeError:
        project = migrate.migrate_project(file)

    self.get_clipboard().clear()
    self.get_view_clipboard().clear()
    figure_settings = self.get_data().get_figure_settings()
    for key, value in project["figure-settings"].items():
        figure_settings.set_property(key, value)
    self.get_data().set_items([item.new_from_dict(d) for d in project["data"]])

    self.get_clipboard().props.data_copy = self.get_data().to_dict()
    self.get_clipboard().set_clipboard(project["data-clipboard"])
    self.get_clipboard().set_clipboard_pos(project["data-clipboard-position"])
    self.get_view_clipboard().set_clipboard(project["view-clipboard"])
    self.get_view_clipboard().set_clipboard_pos(
        project["view-clipboard-position"],
    )
    ui.set_clipboard_buttons(self)
    ui.reload_canvas(self)
