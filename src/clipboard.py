# SPDX-License-Identifier: GPL-3.0-or-later
from graphs import graphs


def reset(self):
    for _key, item in self.datadict.items():
        item.xdata_clipboard = [item.xdata]
        item.ydata_clipboard = [item.ydata]
        item.clipboard_pos = -1
    win = self.main_window
    win.redo_button.set_sensitive(False)
    win.undo_button.set_sensitive(False)


def add(self):
    """
    Add data to the clipboard, is performed whenever an action is performed.
    Appends the latest state to the clipboard.
    """
    undo_button = self.main_window.undo_button
    undo_button.set_sensitive(True)

    # If a couple of redo"s were performed previously, it deletes the clipboard
    # data that is located after the current clipboard position and disables
    # the redo button
    for _key, item in self.datadict.items():
        delete_lists = - item.clipboard_pos - 1
        for _index in range(delete_lists):
            del item.xdata_clipboard[-1]
            del item.ydata_clipboard[-1]
        if delete_lists != 0:
            redo_button = self.main_window.redo_button
            redo_button.set_sensitive(False)

        item.clipboard_pos = -1
        item.xdata_clipboard.append(item.xdata.copy())
        item.ydata_clipboard.append(item.ydata.copy())


def undo(self):
    """
    Undo an action, moves the clipboard position backwards by one and changes
    the dataset to the state before the previous action was performed
    """
    undo_button = self.main_window.undo_button
    redo_button = self.main_window.redo_button
    for _key, item in self.datadict.items():
        if abs(item.clipboard_pos) < len(item.xdata_clipboard):
            redo_button.set_sensitive(True)
            item.xdata = item.xdata_clipboard[item.clipboard_pos].copy()
            item.ydata = item.ydata_clipboard[item.clipboard_pos].copy()
            item.clipboard_pos -= 1
    if abs(item.clipboard_pos) >= len(item.xdata_clipboard):
        undo_button.set_sensitive(False)
    graphs.refresh(self)


def redo(self):
    """
    Redo an action, moves the clipboard position forwards by one and changes
    the dataset to the state before the previous action was undone
    """
    undo_button = self.main_window.undo_button
    redo_button = self.main_window.redo_button
    for _key, item in self.datadict.items():
        if item.clipboard_pos < 0:
            undo_button.set_sensitive(True)
            item.clipboard_pos += 1
            item.xdata = item.xdata_clipboard[item.clipboard_pos].copy()
            item.ydata = item.ydata_clipboard[item.clipboard_pos].copy()
    if item.clipboard_pos >= -1:
        redo_button.set_sensitive(False)
    graphs.refresh(self)
