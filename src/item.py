# SPDX-License-Identifier: GPL-3.0-or-later
import uuid


class Item:
    def __init__(self, config, xdata, ydata, name="", color=(0, 0, 0),
            markerstyle="none"):
        self.key: str = str(uuid.uuid4())
        self.name = name
        self.plot_y_position = config["plot_y_position"]
        self.plot_x_position = config["plot_x_position"]
        self.selected = True
        self.color = color
        self.xdata = xdata
        self.ydata = ydata
        self.clipboard_pos = -1
        self.xdata_clipboard = [self.xdata.copy()]
        self.ydata_clipboard = [self.ydata.copy()]
        self.markerstyle = markerstyle
