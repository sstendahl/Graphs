import copy

from gi.repository import Adw, GObject

from graphs import item, ui

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
            self.perform_undo()
        ui.set_clipboard_buttons(self.props.application)

    def redo(self):
        """
        Redo an action, moves the clipboard position forwards by one and
        changes the dataset to the state before the previous action was undone
        """
        if self.props.clipboard_pos < -1:
            self.props.clipboard_pos += 1
            self.perform_redo()
        ui.set_clipboard_buttons(self.props.application)

    def clear(self):
        self.__init__(self.props.application)


class DataClipboard(BaseClipboard):
    __gtype_name__ = "DataClipboard"

    current_batch = GObject.Property(type=object)
    data_copy = GObject.Property(type=object)

    def __init__(self, application):
        super().__init__(
            application=application, current_batch=[], data_copy={},
            clipboard=[([], application.props.figure_settings.get_limits())],
        )

    def add(self):
        """
        Add data to the clipboard, is performed whenever an action is performed
        Appends the latest state to the clipboard.
        """
        if not self.props.current_batch:
            return
        super().add((
            self.props.current_batch,
            self.props.application.props.figure_settings.get_limits(),
        ))
        # Keep clipboard length limited to 100 spots
        if len(self.props.clipboard) > 101:
            self.props.clipboard = self.props.clipboard[1:]
        self.props.current_batch = []
        self.props.data_copy = copy.deepcopy(
            self.props.application.props.data.to_dict(),
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
            self.props.application.props.data.to_dict(),
        )
        self.props.application.props.view_clipboard.add()

    def redo(self):
        """
        Redo an action, moves the clipboard position forwards by one and
        changes the dataset to the state before the previous action was undone
        """
        super().redo()
        self.props.current_batch = []
        self.props.data_copy = copy.deepcopy(
            self.props.application.props.data.to_dict(),
        )
        self.props.application.props.view_clipboard.add()

    def perform_undo(self):
        batch = self.props.clipboard[self.props.clipboard_pos + 1][0]
        data = self.props.application.props.data
        items_changed = False
        for change_type, change in reversed(batch):
            if change_type == 0:
                data[change[0]].set_property(change[1], change[2])
            elif change_type == 1:
                data.pop(change["key"])
                items_changed = True
            elif change_type == 2:
                item_ = item.new_from_dict(change[1])
                data.append(item_)
                data.change_position(data.get_keys()[change[0]], item_.key)
                items_changed = True
            elif change_type == 3:
                data.change_position(data[change[0]].key, data[change[1]].key)
                items_changed = True
        if items_changed:
            data.notify("items")
        data.notify("items_selected")
        self.props.application.props.figure_settings.set_limits(
            self.props.clipboard[self.props.clipboard_pos][1],
        )

    def perform_redo(self):
        state = self.props.clipboard[self.props.clipboard_pos]
        data = self.props.application.props.data
        items_changed = False
        for change_type, change in state[0]:
            if change_type == 0:
                data[change[0]].set_property(change[1], change[3])
            elif change_type == 1:
                data.append(item.new_from_dict(change))
                items_changed = True
            elif change_type == 2:
                data.pop(change[1]["key"])
                items_changed = True
            elif change_type == 3:
                data.change_position(data[change[1]].key, data[change[0]].key)
                items_changed = True
        if items_changed:
            data.notify("items")
        data.notify("items_selected")
        self.props.application.props.figure_settings.set_limits(state[1])

    def on_item_change(self, item_, param):
        self.props.current_batch.append((0, (
            item_.key, param.name, self.props.data_copy[item_.key][param.name],
            item_.get_property(param.name),
        )))


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
            not numpy.isclose(value, limits[count])
            for count, value in enumerate(self.props.clipboard[-1])
        )
        if view_changed:
            super().add(limits)

    def perform_undo(self):
        self._set_clipboard_state()

    def perform_redo(self):
        self._set_clipboard_state()

    def _set_clipboard_state(self):
        self.props.application.props.figure_settings.set_limits(
            self.props.clipboard[self.props.clipboard_pos],
        )
