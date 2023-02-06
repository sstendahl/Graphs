# SPDX-License-Identifier: GPL-3.0-or-later
import uuid
from dataclasses import dataclass, field

@dataclass
class Data:
    filename: str = ""
    clipboard_pos: int = 0
    xdata: list = field(default_factory=list)
    ydata: list = field(default_factory=list)
    xdata_selected: list = field(default_factory=list)
    ydata_selected: list = field(default_factory=list)
    xdata_clipboard: list = field(default_factory=list)
    ydata_clipboard: list = field(default_factory=list)
    linestyle_selected: str = ""
    linestyle_unselected: str = ""
    selected_line_thickness: float = 0
    unselected_line_thickness: float = 0
    selected_markers: str = ""
    unselected_markers: str = ""
    selected_marker_size: float = 0
    unselected_marker_size: float = 0
    plot_Y_position: str = "left"
    plot_X_position: str = "bottom"
    selected: bool = True
    
    def __init__(self):
        self.id: str = str(uuid.uuid4())
