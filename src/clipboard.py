from gi.repository import Adw, GObject

from graphs import graphs, item, ui


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
            clipboard=[{"data": [],
                        "view": application.canvas.limits}],
        )

    def add(self):
        """
        Add data to the clipboard, is performed whenever an action is performed
        Appends the latest state to the clipboard.
        """
        items = self.props.application.datadict.values()
        super().add({"data": [item.to_dict() for item in items],
                     "view": self.props.application.canvas.limits})
        # Keep clipboard length limited to preference values
        max_clipboard_length = \
            self.props.application.props.settings.get_int("clipboard-length")
        if len(self.props.clipboard) > max_clipboard_length + 1:
            self.props.clipboard = self.props.clipboard[1:]

    def undo(self):
        """
        Undo an action, moves the clipboard position backwards by one and
        changes the dataset to the state before the previous action was
        performed
        """
        super().undo()
        graphs.check_open_data(self.props.application)
        ui.reload_item_menu(self.props.application)
        self.props.application.ViewClipboard.add()

    def redo(self):
        """
        Redo an action, moves the clipboard position forwards by one and
        changes the dataset to the state before the previous action was undone
        """
        super().redo()
        graphs.check_open_data(self.props.application)
        ui.reload_item_menu(self.props.application)
        self.props.application.ViewClipboard.add()

    def set_clipboard_state(self):
        state = self.props.clipboard[self.props.clipboard_pos]
        items = [item.new_from_dict(d) for d in state["data"]]
        self.props.application.datadict = {item.key: item for item in items}
        if self.props.application.ViewClipboard.view_changed:
            self.props.application.canvas.limits = state["view"]


class ViewClipboard(BaseClipboard):
    __gtype_name__ = "ViewClipboard"

    view_changed = GObject.Property(type=bool, default=False)

    def __init__(self, application):
        super().__init__(
            application=application,
            clipboard=[application.canvas.limits],
        )

    def add(self):
        """
        Add the latest view to the clipboard, skip in case the new view is
        the same as previous one (e.g. if an action does not change the limits)
        """
        self.props.view_changed = False
        if self.props.application.canvas.limits != self.props.clipboard[-1]:
            super().add(self.props.application.canvas.limits)
            self.props.view_changed = True

    def redo(self):
        """Go back to the next view"""
        super().redo()
        self.props.application.canvas.limits = \
            self.props.clipboard[self.props.clipboard_pos]

    def set_clipboard_state(self):
        self.props.application.canvas.limits = \
            self.props.clipboard[self.props.clipboard_pos]
