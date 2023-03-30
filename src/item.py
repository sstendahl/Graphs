# SPDX-License-Identifier: GPL-3.0-or-later
import uuid


class Item:
    def __init__(self, config, xdata, ydata, name="", color=(0, 0, 0)):
        self.name = name
        self.plot_y_position = config["plot_y_position"]
        self.plot_x_position = config["plot_x_position"]
        self.linestyle_selected = config["plot_selected_linestyle"]
        self.linestyle_unselected = config["plot_unselected_linestyle"]
        self.selected_line_thickness = config["selected_linewidth"]
        self.unselected_line_thickness = config["unselected_linewidth"]
        self.selected_markers = config["plot_selected_markers"]
        self.unselected_markers = config["plot_unselected_markers"]
        self.selected_marker_size = config["plot_selected_marker_size"]
        self.unselected_marker_size = config["plot_unselected_marker_size"]
        self.selected_marker_size = float(0)
        self.unselected_marker_size = float(0)
        self.selected = True
        self.color = color
        self.xdata = xdata
        self.ydata = ydata
        self.clipboard_pos = -1
        self.xdata_clipboard = [self.xdata.copy()]
        self.ydata_clipboard = [self.ydata.copy()]
        self.key: str = str(uuid.uuid4())
