# SPDX-License-Identifier: GPL-3.0-or-later
import copy

from graphs import graphs, ui


def add(self):
    """
    Add data to the clipboard, is performed whenever an action is performed.
    Appends the latest state to the clipboard.
    """
    self.main_window.undo_button.set_sensitive(True)

    # If a couple of redo"s were performed previously, it deletes the clipboard
    # data that is located after the current clipboard position and disables
    # the redo button
    if self.clipboard_pos != -1:
        self.datadict_clipboard = \
            self.datadict_clipboard[:self.clipboard_pos + 1]

    self.clipboard_pos = -1
    self.datadict_clipboard.append(copy.deepcopy(self.datadict))
    if len(self.datadict_clipboard) > \
            self.preferences.config["clipboard_length"] + 1:
        self.datadict_clipboard = \
            self.datadict_clipboard[1:]

    self.main_window.redo_button.set_sensitive(False)


def undo(self):
    """
    Undo an action, moves the clipboard position backwards by one and changes
    the dataset to the state before the previous action was performed
    """
    if abs(self.clipboard_pos) < len(self.datadict_clipboard):
        self.clipboard_pos -= 1
        self.datadict = \
            copy.deepcopy(self.datadict_clipboard[self.clipboard_pos])

    if abs(self.clipboard_pos) >= len(self.datadict_clipboard):
        self.main_window.undo_button.set_sensitive(False)
    if self.clipboard_pos < -1:
        self.main_window.redo_button.set_sensitive(True)
    graphs.reload(self)
    graphs.check_open_data(self)
    ui.reload_item_menu(self)



def redo(self):
    """
    Redo an action, moves the clipboard position forwards by one and changes
    the dataset to the state before the previous action was undone
    """
    if self.clipboard_pos < -1:
        self.clipboard_pos += 1
        self.datadict = \
            copy.deepcopy(self.datadict_clipboard[self.clipboard_pos])
        self.main_window.undo_button.set_sensitive(True)

    if self.clipboard_pos >= -1:
        self.main_window.redo_button.set_sensitive(False)
    graphs.reload(self)
    graphs.check_open_data(self)
    ui.reload_item_menu(self)
