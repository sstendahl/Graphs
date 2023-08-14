# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gio

from graphs import file_io, migrate, plotting_tools, ui
from graphs.figure_settings import FigureSettings


def save_project(self, file: Gio.File):
    file_io.write_json(file, {
        "version": self.version,
        "data": self.props.data.to_list(),
        "figure-settings": self.props.figure_settings.to_dict(),
        "data-clipboard": self.props.clipboard.props.clipboard,
        "data-clipboard-position": self.props.clipboard.props.clipboard_pos,
        "view-clipboard": self.props.view_clipboard.props.clipboard,
        "view-clipboard-position":
            self.props.view_clipboard.props.clipboard_pos,
    })


def load_project(self, file: Gio.File):
    try:
        project = file_io.parse_json(file)
    except UnicodeDecodeError:
        project = migrate.migrate_project(file)

    self.props.clipboard.clear()
    self.props.view_clipboard.clear()
    self.props.figure_settings = \
        FigureSettings.new_from_dict(project["figure-settings"])
    self.props.data.set_from_list(project["data"])

    self.props.clipboard.props.clipboard = project["data-clipboard"]
    self.props.clipboard.props.clipboard_pos = \
        project["data-clipboard-position"]

    # migrated project
    if project["view-clipboard"] is None:
        plotting_tools.optimize_limits(self)
        self.props.view_clipboard.add()
    else:
        clipboard = project["view-clipboard"]
        clipboard_pos = project["view-clipboard-position"]
        self.props.view_clipboard.props.clipboard = clipboard
        self.props.view_clipboard.props.clipboard_pos = clipboard_pos
        self.props.figure_settings.set_limits(clipboard[-1])
    ui.set_clipboard_buttons(self)
    self.main_window.reload_canvas()
