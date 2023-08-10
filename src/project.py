# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Gio

from graphs import file_io, graphs, item, ui, migrate, plotting_tools
from graphs.plot_settings import FigureSettings


def save_project(self, file: Gio.File):
    file_io.write_json(file, {
        "version": self.version,
        "data": [item.to_dict() for item in self.datadict.values()],
        "figure-settings": self.props.figure_settings.to_dict(),
        "data-clipboard": self.Clipboard.props.clipboard,
        "data-clipboard-position": self.Clipboard.props.clipboard_pos,
        "view-clipboard": self.ViewClipboard.props.clipboard,
        "view-clipboard-position": self.ViewClipboard.props.clipboard_pos,
    })


def load_project(self, file: Gio.File):
    try:
        project = file_io.parse_json(file)
    except UnicodeDecodeError:
        project = migrate.migrate_project(file)

    self.Clipboard.clear()
    self.ViewClipboard.clear()
    self.props.figure_settings = \
        FigureSettings.new_from_dict(project["figure-settings"])
    items = [item.new_from_dict(d) for d in project["data"]]
    self.datadict = {item.key: item for item in items}

    self.Clipboard.props.clipboard = project["data-clipboard"]
    self.Clipboard.props.clipboard_pos = project["data-clipboard-position"]
    self.ViewClipboard.props.clipboard = project["view-clipboard"]
    self.ViewClipboard.props.clipboard_pos = project["view-clipboard-position"]

    try:
        self.canvas.limits = self.ViewClipboard.props.clipboard[-1]
    except IndexError:
        self.ViewClipboard.clipboard = [migrate.DEFAULT_VIEW.copy()]
        plotting_tools.optimize_limits(self)
    self.canvas.apply_limits()
    ui.reload_item_menu(self)
    ui.enable_data_dependent_buttons(self)
    ui.set_clipboard_buttons(self)
    graphs.reload(self)
