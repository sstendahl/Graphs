from gi.repository import Adw, GObject, Graphs

from graphs import ui

import numpy


class Clipboard(GObject.Object, Graphs.ClipboardInterface):
    __gtype_name__ = "GraphsClipboard"

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
        if self.get_clipboard_pos() != -1:
            self.set_clipboard(
                self.get_clipboard()[:self.get_clipboard_pos() + 1],
            )
        self.props.clipboard_pos = -1
        self.get_clipboard().append(new_state)
        ui.set_clipboard_buttons(self.get_application())

    def undo(self):
        if abs(self.get_clipboard_pos()) < len(self.get_clipboard()):
            self.props.clipboard_pos -= 1
            self.perform_undo()
            ui.set_clipboard_buttons(self.get_application())

    def redo(self):
        """
        Redo an action, moves the clipboard position forwards by one and
        changes the dataset to the state before the previous action was undone
        """
        if self.get_clipboard_pos() < -1:
            self.props.clipboard_pos += 1
            self.perform_redo()
            ui.set_clipboard_buttons(self.get_application())

    def clear(self):
        self.__init__(self.get_application())

    def get_application(self):
        """Get application property."""
        return self.props.application

    def get_clipboard(self) -> list:
        """Get clipboard property."""
        return self.props.clipboard

    def set_clipboard(self, clipboard: list):
        """Set clipboard property."""
        self.props.clipboard = clipboard

    def get_clipboard_pos(self) -> int:
        """Get clipboard position property."""
        return self.props.clipboard_pos

    def set_clipboard_pos(self, clipboard_pos: int):
        """Get clipboard position property."""
        self.props.clipboard_pos = clipboard_pos


class ViewClipboard(Clipboard):
    __gtype_name__ = "GraphsViewClipboard"

    def __init__(self, application):
        super().__init__(
            application=application,
            clipboard=[
                application.get_data().get_figure_settings().get_limits(),
            ],
        )

    def add(self):
        """
        Add the latest view to the clipboard, skip in case the new view is
        the same as previous one (e.g. if an action does not change the limits)
        """
        limits = self.get_application().get_data().get_figure_settings(
        ).get_limits()
        view_changed = any(
            not numpy.isclose(value, limits[count])
            for count, value in enumerate(self.get_clipboard()[-1])
        )
        if view_changed:
            super().add(limits)

    def perform_undo(self):
        self._set_clipboard_state()

    def perform_redo(self):
        self._set_clipboard_state()

    def _set_clipboard_state(self):
        self.get_application().get_data().get_figure_settings().set_limits(
            self.get_clipboard()[self.get_clipboard_pos()],
        )
