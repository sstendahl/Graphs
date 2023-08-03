import copy

from graphs import graphs, ui


class BaseClipboard:
    def __init__(self, application):
        self.application = application
        self.clipboard = []
        self.clipboard_pos = -1

    def add(self, new_state):
        # If a couple of redo's were performed previously, it deletes the
        # clipboard data that is located after the current clipboard position
        # and disables the redo button
        if self.clipboard_pos != -1:
            self.clipboard = \
                self.clipboard[:self.clipboard_pos + 1]
        self.clipboard_pos = -1
        self.clipboard.append(new_state)
        ui.set_clipboard_buttons(self.application)

    def undo(self):
        if abs(self.clipboard_pos) < len(self.clipboard):
            self.clipboard_pos -= 1
            self.set_clipboard_state()
        ui.set_clipboard_buttons(self.application)

    def redo(self):
        """
        Redo an action, moves the clipboard position forwards by one and
        changes the dataset to the state before the previous action was undone
        """
        if self.clipboard_pos < -1:
            self.clipboard_pos += 1
            self.set_clipboard_state()
        ui.set_clipboard_buttons(self.application)

    def __setitem__(self, key, value):
        """Allow to set the attributes in the Clipboard like a dictionary"""
        setattr(self, key, value)

    def clear(self):
        self.__init__(self.application)


class DataClipboard(BaseClipboard):
    def __init__(self, application):
        super().__init__(application)
        self.clipboard = [{"datadict": {},
                           "view": self.application.canvas.limits}]
        self.undo_button = self.application.main_window.undo_button
        self.redo_button = self.application.main_window.redo_button

    def add(self):
        """
        Add data to the clipboard, is performed whenever an action is performed
        Appends the latest state to the clipboard.
        """
        data = {"datadict": copy.deepcopy(self.application.datadict),
                "view": self.application.canvas.limits}
        super().add(copy.deepcopy(data))
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
        super().undo()
        graphs.check_open_data(self.application)
        ui.reload_item_menu(self.application)
        self.application.ViewClipboard.add()

    def redo(self):
        """
        Redo an action, moves the clipboard position forwards by one and
        changes the dataset to the state before the previous action was undone
        """
        super().redo()
        graphs.check_open_data(self.application)
        ui.reload_item_menu(self.application)
        self.application.ViewClipboard.add()

    def set_clipboard_state(self):
        self.application.datadict = \
            copy.deepcopy(self.clipboard[self.clipboard_pos]["datadict"])
        if self.application.ViewClipboard.view_changed:
            self.application.canvas.limits = \
                self.clipboard[self.clipboard_pos]["view"]


class ViewClipboard(BaseClipboard):

    def __init__(self, application):
        super().__init__(application)
        self.clipboard = [self.application.canvas.limits]
        self.undo_button = self.application.main_window.view_back_button
        self.redo_button = self.application.main_window.view_forward_button
        self.view_changed = False

    def add(self):
        """
        Add the latest view to the clipboard, skip in case the new view is
        the same as previous one (e.g. if an action does not change the limits)
        """
        self.view_changed = False
        if self.application.canvas.limits != self.clipboard[-1]:
            super().add(self.application.canvas.limits)
            self.view_changed = True

    def redo(self):
        """Go back to the next view"""
        super().redo()
        self.application.canvas.limits = self.clipboard[self.clipboard_pos]

    def set_clipboard_state(self):
        self.application.canvas.limits = self.clipboard[self.clipboard_pos]
