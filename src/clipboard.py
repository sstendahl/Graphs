from gi.repository import Adw, GObject

from graphs import ui

import copy

import numpy


class BaseClipboard(GObject.Object):
    __gtype_name__ = "BaseClipboard"

    application = GObject.Property(type=Adw.Application)
    clipboard = GObject.Property(type=object)
    clipboard_pos = GObject.Property(type=int, default=-1)

    def __init__(self, clipboard=None, **kwargs):
        if clipboard is None:
            clipboard = []
        super().__init__(clipboard=clipboard, **kwargs)

    def add(self, new_state):
        # If a couple of redo's were performed previously, it deletes the
        # clipboard data that is located after the current clipboard position
        # and disables the redo button
        if self.props.clipboard_pos != -1:
            self.props.clipboard = \
                self.props.clipboard[:self.props.clipboard_pos + 1]
        self.props.clipboard_pos = -1
        self.props.clipboard.append(new_state)
        ui.set_clipboard_buttons(self.props.application)

    def undo(self):
        if abs(self.props.clipboard_pos) < len(self.props.clipboard):
            self.props.clipboard_pos -= 1
            self.set_clipboard_state()
        ui.set_clipboard_buttons(self.props.application)

    def redo(self):
        """
        Redo an action, moves the clipboard position forwards by one and
        changes the dataset to the state before the previous action was undone
        """
        if self.props.clipboard_pos < -1:
            self.props.clipboard_pos += 1
            self.set_clipboard_state()
        ui.set_clipboard_buttons(self.props.application)

    def clear(self):
        self.__init__(self.props.application)


class DataClipboard(BaseClipboard):
    __gtype_name__ = "DataClipboard"

    def __init__(self, application):
        super().__init__(
            application=application,
            clipboard=[{
                "data": [],
                "view": application.props.figure_settings.get_limits(),
            }],
        )

    def add(self):
        """
        Add data to the clipboard, is performed whenever an action is performed
        Appends the latest state to the clipboard.
        """
        super().add({
            "data": copy.deepcopy(self.props.application.props.data.to_list()),
            "view": self.props.application.props.figure_settings.get_limits(),
        })
        # Keep clipboard length limited to preference values
        max_clipboard_length = \
            self.props.application.get_settings().get_int("clipboard-length")
        if len(self.props.clipboard) > max_clipboard_length + 1:
            self.props.clipboard = self.props.clipboard[1:]

    def undo(self):
        """
        Undo an action, moves the clipboard position backwards by one and
        changes the dataset to the state before the previous action was
        performed
        """
        super().undo()
        self.props.application.props.view_clipboard.add()

    def redo(self):
        """
        Redo an action, moves the clipboard position forwards by one and
        changes the dataset to the state before the previous action was undone
        """
        super().redo()
        self.props.application.props.view_clipboard.add()

    def set_clipboard_state(self):
        state = self.props.clipboard[self.props.clipboard_pos]
        self.props.application.props.data.set_from_list(state["data"])
        self.props.application.props.figure_settings.set_limits(state["view"])


class ViewClipboard(BaseClipboard):
    __gtype_name__ = "ViewClipboard"

    def __init__(self, application):
        super().__init__(
            application=application,
            clipboard=[application.props.figure_settings.get_limits()],
        )

    def add(self):
        """
        Add the latest view to the clipboard, skip in case the new view is
        the same as previous one (e.g. if an action does not change the limits)
        """
        limits = self.props.application.props.figure_settings.get_limits()
        view_changed = all(
            not numpy.isclose(value, limits[key])
            for key, value in self.props.clipboard[-1].items()
        )
        if view_changed:
            super().add(limits)

    def set_clipboard_state(self):
        self.props.application.props.figure_settings.set_limits(
            self.props.clipboard[self.props.clipboard_pos],
        )
