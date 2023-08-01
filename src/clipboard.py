import copy
from graphs import graphs, ui
from typing import Any


class BaseClipboard:
    def __init__(self, application):
        self.application = application
        self.clipboard = []
        self.clipboard_pos = -1

    def add(self, new_state):
        self.undo_button.set_sensitive(True)
        # If a couple of redo"s were performed previously, it deletes the
        # clipboard data that is located after the current clipboard position
        # and disables the redo button
        if self.clipboard_pos != -1:
            self.clipboard = \
                self.clipboard[:self.clipboard_pos + 1]
        self.clipboard_pos = -1
        self.clipboard.append(new_state)
        self.redo_button.set_sensitive(False)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow to set the attributes in the Clipboard like a dictionary"""
        setattr(self, key, value)


class DataClipboard(BaseClipboard):
    def __init__(self, application):
        super().__init__(application)
        self.clipboard = [{}]
        self.undo_button = self.application.main_window.undo_button
        self.redo_button = self.application.main_window.redo_button

    def add(self):
        """
        Add data to the clipboard, is performed whenever an action is performed
        Appends the latest state to the clipboard.
        """
        super().add(copy.deepcopy(self.application.datadict))
        # Keep clipboard length limited to preference values
        if len(self.clipboard) > \
                int(self.application.preferences["clipboard_length"]) + 1:
            self.clipboard = self.clipboard[1:]

    def undo(self):
        """
        Undo an action, moves the clipboard position backwards by one and
        changes the dataset to the state before the previous action was
        performed
        """

        if abs(self.clipboard_pos) < len(self.clipboard):
            self.clipboard_pos -= 1
            self.application.datadict = \
                copy.deepcopy(self.clipboard[self.clipboard_pos])

            if abs(self.clipboard_pos) >= len(self.clipboard):
                self.application.main_window.undo_button.set_sensitive(False)
            if self.clipboard_pos < -1:
                self.application.main_window.redo_button.set_sensitive(True)
            graphs.check_open_data(self.application)
            ui.reload_item_menu(self.application)
            if self.application.ViewClipboard.view_changed:
                self.application.ViewClipboard.undo()

    def redo(self):

        """
        Redo an action, moves the clipboard position forwards by one and
        changes the dataset to the state before the previous action was undone
        """

        if self.clipboard_pos < -1:
            self.clipboard_pos += 1
            self.application.datadict = \
                copy.deepcopy(self.clipboard[self.clipboard_pos])
            self.application.main_window.undo_button.set_sensitive(True)

        if self.clipboard_pos >= -1:
            self.application.main_window.redo_button.set_sensitive(False)
        graphs.check_open_data(self.application)
        ui.reload_item_menu(self.application)
        if self.application.ViewClipboard.view_changed:
            self.application.ViewClipboard.redo()

    def clear(self):

        """Clear the clipboard to the initial state"""
        self.clipboard = [{}]
        self.clipboard_pos = -1


class ViewClipboard(BaseClipboard):

    def __init__(self, application):

        super().__init__(application)
        self.clipboard = [self.application.canvas.get_limits()]
        self.undo_button = self.application.main_window.view_back_button
        self.redo_button = self.application.main_window.view_forward_button
        self.view_changed = False

    def add(self):

        """
        Add the latest view to the clipboard, skip in case the new view is
        the same as previous one (e.g. if an action does not change the limits)
        """
        self.view_changed = False
        if self.application.canvas.get_limits() != self.clipboard[-1]:
            super().add(self.application.canvas.get_limits())
            self.view_changed = True

    def undo(self):

        """Go back to the previous view"""
        if abs(self.clipboard_pos) < len(self.clipboard):
            self.clipboard_pos -= 1
            self.application.canvas.set_limits(
                self.clipboard[self.clipboard_pos])

        if abs(self.clipboard_pos) >= len(self.clipboard):
            self.application.main_window.view_back_button.set_sensitive(False)
        if self.clipboard_pos < -1:
            self.application.main_window.view_forward_button.set_sensitive(
                True)
        self.application.canvas.set_limits(
            self.clipboard[self.clipboard_pos])

    def redo(self):

        """Go back to the next view"""

        if self.clipboard_pos < -1:
            self.clipboard_pos += 1
            self.application.canvas.set_limits(
                self.clipboard[self.clipboard_pos])
            self.application.main_window.view_back_button.set_sensitive(True)

        if self.clipboard_pos >= -1:
            self.application.main_window.view_forward_button.set_sensitive(
                False)
        self.application.canvas.set_limits(
            self.clipboard[self.clipboard_pos])

    def clear(self):
        """Clear the clipboard to the initial state"""
        self.clipboard = [self.application.canvas.get_limits()]
        self.clipboard_pos = -1
