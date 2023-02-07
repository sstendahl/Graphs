# SPDX-License-Identifier: GPL-3.0-or-later
import uuid
import os
from . import graphs
from dataclasses import dataclass, field

@dataclass
class Data:
    filename: str = ""
    clipboard_pos: int = 0
    xdata_selected: list = field(default_factory=list)
    ydata_selected: list = field(default_factory=list)
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
    color: str = ""
    
    def __init__(self, parent, xdata, ydata, import_settings = None):
        self.xdata = xdata
        self.ydata = ydata
        self.clipboard_pos = 0
        self.xdata_clipboard = [self.xdata.copy()]
        self.ydata_clipboard = [self.ydata.copy()]
        self.id: str = str(uuid.uuid4())
        if import_settings is None:
            import_settings = graphs.get_import_settings(parent) 
        self.set_data_properties(parent, import_settings)
                    
    def set_data_properties(self, parent, import_settings):
        self.plot_Y_position = parent.preferences.config["plot_Y_position"]
        self.plot_X_position = parent.preferences.config["plot_X_position"]    
        self.linestyle_selected = parent.preferences.config["plot_selected_linestyle"]
        self.linestyle_unselected = parent.preferences.config["plot_unselected_linestyle"]
        self.selected_line_thickness = parent.preferences.config["selected_linewidth"]
        self.unselected_line_thickness = parent.preferences.config["unselected_linewidth"]
        self.selected_markers = parent.preferences.config["plot_selected_markers"]
        self.unselected_markers = parent.preferences.config["plot_unselected_markers"]
        self.selected_marker_size = parent.preferences.config["plot_selected_marker_size"]
        self.unselected_marker_size = parent.preferences.config["plot_unselected_marker_size"]        
        if import_settings["name"] != "" and import_settings["mode"] == "single":
            filename = import_settings["name"]
        else:
            filename = import_settings["path"].split("/")[-1]
            filename = os.path.splitext(filename)[0]
        self.filename = filename          
       
