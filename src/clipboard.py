import copy

from gi.repository import Adw, GObject, Graphs

from graphs import item, ui

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


class DataClipboard(Clipboard):
    __gtype_name__ = "GraphsDataClipboard"

    current_batch = GObject.Property(type=object)
    data_copy = GObject.Property(type=object)

    def __init__(self, application):
        super().__init__(
            application=application, current_batch=[], data_copy={},
            clipboard=[([], application.get_figure_settings().get_limits())],
        )

    def add(self, old_limits=None):
        """
        Add data to the clipboard, is performed whenever an action is performed
        Appends the latest state to the clipboard.
        """
        if not self.props.current_batch:
            return
        super().add((
            self.props.current_batch,
            self.get_application().get_figure_settings().get_limits(),
        ))

        if old_limits is not None:
            for index in range(8):
                self.get_clipboard()[self.get_clipboard_pos() - 1][1][index] \
                    = old_limits[index]
        # Keep clipboard length limited to 100 spots
        if len(self.get_clipboard()) > 101:
            self.set_clipboard(self.get_clipboard()[1:])
        self.props.current_batch = []
        self.props.data_copy = copy.deepcopy(
            self.get_application().get_data().to_dict(),
        )

    def undo(self):
        """
        Undo an action, moves the clipboard position backwards by one and
        changes the dataset to the state before the previous action was
        performed
        """
        super().undo()
        self.props.current_batch = []
        self.props.data_copy = copy.deepcopy(
            self.get_application().get_data().to_dict(),
        )
        self.get_application().get_view_clipboard().add()

    def redo(self):
        """
        Redo an action, moves the clipboard position forwards by one and
        changes the dataset to the state before the previous action was undone
        """
        super().redo()
        self.props.current_batch = []
        self.props.data_copy = copy.deepcopy(
            self.get_application().get_data().to_dict(),
        )
        self.get_application().get_view_clipboard().add()

    def perform_undo(self):
        batch = self.get_clipboard()[self.get_clipboard_pos() + 1][0]
        data = self.get_application().get_data()
        items_changed = False
        for change_type, change in reversed(batch):
            if change_type == 0:
                data[change[0]].set_property(change[1], change[2])
            elif change_type == 1:
                data.pop(change["uuid"])
                items_changed = True
            elif change_type == 2:
                item_ = item.new_from_dict(change[1])
                data.append(item_)
                data.change_position(change[0], len(data))
                items_changed = True
            elif change_type == 3:
                data.change_position(change[0], change[1])
                items_changed = True
        if items_changed:
            data.notify("items")
        data.notify("items_selected")
        self.get_application().get_figure_settings().set_limits(
            self.get_clipboard()[self.get_clipboard_pos()][1],
        )

    def perform_redo(self):
        state = self.get_clipboard()[self.get_clipboard_pos()]
        data = self.get_application().get_data()
        items_changed = False
        for change_type, change in state[0]:
            if change_type == 0:
                data[change[0]].set_property(change[1], change[3])
            elif change_type == 1:
                data.append(item.new_from_dict(change))
                items_changed = True
            elif change_type == 2:
                data.pop(change[1]["uuid"])
                items_changed = True
            elif change_type == 3:
                data.change_position(change[1], change[0])
                items_changed = True
        if items_changed:
            data.notify("items")
        data.notify("items_selected")
        self.get_application().get_figure_settings().set_limits(state[1])

    def on_item_change(self, item_, param):
        self.append((0, (
            item_.get_uuid(), param.name,
            copy.deepcopy(self.props.data_copy[item_.get_uuid()][param.name]),
            copy.deepcopy(item_.get_property(param.name)),
        )))

    def append(self, change):
        self.props.current_batch.append(change)


class ViewClipboard(Clipboard):
    __gtype_name__ = "GraphsViewClipboard"

    def __init__(self, application):
        super().__init__(
            application=application,
            clipboard=[application.get_figure_settings().get_limits()],
        )

    def add(self):
        """
        Add the latest view to the clipboard, skip in case the new view is
        the same as previous one (e.g. if an action does not change the limits)
        """
        limits = self.get_application().get_figure_settings().get_limits()
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
        self.get_application().get_figure_settings().set_limits(
            self.get_clipboard()[self.get_clipboard_pos()],
        )
