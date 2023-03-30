# SPDX-License-Identifier: GPL-3.0-or-later
import os
import uuid

from graphs.misc import ImportMode, ImportSettings


class Data:
    def __init__(self, parent, xdata, ydata, import_settings=None):
        cfg = parent.preferences.config
        self.plot_y_position = cfg["plot_y_position"]
        self.plot_x_position = cfg["plot_x_position"]
        self.linestyle_selected = cfg["plot_selected_linestyle"]
        self.linestyle_unselected = cfg["plot_unselected_linestyle"]
        self.selected_line_thickness = cfg["selected_linewidth"]
        self.unselected_line_thickness = cfg["unselected_linewidth"]
        self.selected_markers = cfg["plot_selected_markers"]
        self.unselected_markers = cfg["plot_unselected_markers"]
        self.selected_marker_size = cfg["plot_selected_marker_size"]
        self.unselected_marker_size = cfg["plot_unselected_marker_size"]
        self.selected_marker_size = float(0)
        self.unselected_marker_size = float(0)
        self.selected = True
        self.color = ""
        self.xdata = xdata
        self.ydata = ydata
        self.clipboard_pos = -1
        self.xdata_clipboard = [self.xdata.copy()]
        self.ydata_clipboard = [self.ydata.copy()]
        self.key: str = str(uuid.uuid4())
        if import_settings is None:
            import_settings = ImportSettings(parent)
        if import_settings.name != "" \
                and import_settings.mode == ImportMode.SINGLE:
            filename = import_settings.name
        else:
            filename = import_settings.path.split("/")[-1]
            filename = os.path.splitext(filename)[0]
        self.filename = filename
