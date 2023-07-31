# SPDX-License-Identifier: GPL-3.0-or-later
import copy

from graphs import graphs, ui


class Clipboard:
    def __init__(self, application):
        self.application = application
        self.datadict_clipboard = [{}]
        self.limits_clipboard = [self.application.canvas.get_limits()]
        self.clipboard_pos = -1

    def __setitem__(self, key, value):
        """Allow to set the attributes in the Clipboard like a dictionary"""
        setattr(self, key, value)

    def add(self):
        """
        Add data to the clipboard, is performed whenever an action is performed
        Appends the latest state to the clipboard.
        """
        self.application.main_window.undo_button.set_sensitive(True)

        # If a couple of redo"s were performed previously, it deletes the
        # clipboard data that is located after the current clipboard position
        # and disables the redo button
        if self.clipboard_pos != -1:
            self.datadict_clipboard = \
                self.datadict_clipboard[:self.clipboard_pos + 1]
            self.limits_clipboard = \
                self.limits_clipboard[:self.clipboard_pos + 1]

        self.clipboard_pos = -1
        self.limits_clipboard.append(self.application.canvas.get_limits())
        self.datadict_clipboard.append(
            copy.deepcopy(self.application.datadict))
        if len(self.datadict_clipboard) > \
                int(self.application.preferences["clipboard_length"]) + 1:
            self.datadict_clipboard = self.datadict_clipboard[1:]
            self.limits_clipboard = self.limits_clipboard[1:]

        self.application.main_window.redo_button.set_sensitive(False)

    def undo(self):
        """
        Undo an action, moves the clipboard position backwards by one and
        changes the dataset to the state before the previous action was
        performed
        """
        if abs(self.clipboard_pos) < len(self.datadict_clipboard):
            self.clipboard_pos -= 1
            self.application.canvas.set_limits(
                self.limits_clipboard[self.clipboard_pos])
            self.application.datadict = \
                copy.deepcopy(self.datadict_clipboard[self.clipboard_pos])

        if abs(self.clipboard_pos) >= len(self.datadict_clipboard):
            self.application.main_window.undo_button.set_sensitive(False)
        if self.clipboard_pos < -1:
            self.application.main_window.redo_button.set_sensitive(True)
        graphs.check_open_data(self.application)
        ui.reload_item_menu(self.application)

    def redo(self):
        """
        Redo an action, moves the clipboard position forwards by one and
        changes the dataset to the state before the previous action was undone
        """
        if self.clipboard_pos < -1:
            self.clipboard_pos += 1
            self.application.datadict = \
                copy.deepcopy(self.datadict_clipboard[self.clipboard_pos])
            self.application.canvas.set_limits(
                self.limits_clipboard[self.clipboard_pos])
            self.application.main_window.undo_button.set_sensitive(True)

        if self.clipboard_pos >= -1:
            self.application.main_window.redo_button.set_sensitive(False)
        graphs.check_open_data(self.application)
        ui.reload_item_menu(self.application)

    def clear(self):
        """Clear the clipboard to the initial state"""
        self.datadict_clipboard = [{}]
        self.limits_clipboard = [self.application.canvas.get_limits()]
        self.clipboard_pos = -1
