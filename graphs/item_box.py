# SPDX-License-Identifier: GPL-3.0-or-later
"""UI representation of an Item."""
from gettext import gettext as _

from gi.repository import Adw, Gio, Graphs

from graphs.curve_fitting import CurveFittingDialog
from graphs.edit_item import EditItemDialog


class ItemBox(Graphs.ItemBox):
    """UI representation of an Item."""

    __gtype_name__ = "GraphsPythonItemBox"

    def __init__(self, application, item, index):
        super().__init__(
            application=application,
            item=item,
            index=index,
        )
        self.setup()
        self.props.drop_target.connect("drop", self.on_dnd_drop)

        action_list = ["edit", "delete", "curve_fitting"]
        if self.props.index > 0:
            action_list += ["move_up"]
        if self.props.index + 1 < len(self.props.application.get_data()):
            action_list += ["move_down"]
        action_group = Gio.SimpleActionGroup()

        # Set the action group for the widget
        for name in action_list:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", getattr(self, f"{name}"))
            action_group.add_action(action)
        self.insert_action_group("item_box", action_group)

    def _change_position(self, source_index: int) -> None:
        data = self.props.application.get_data()
        data.change_position(self.props.index, source_index)
        data.add_history_state()
        data.add_view_history_state()

    def on_dnd_drop(self, _drop_target, value: int, _x, _y) -> None:
        """Handle dropped data."""
        self._change_position(value)

    def curve_fitting(self, _action, _shortcut) -> None:
        """Open Curve Fitting dialog."""
        CurveFittingDialog(self.props.application, self.props.item)

    def move_up(self, _action, _shortcut) -> None:
        """Move item up in hirarchy."""
        self._change_position(self.props.index - 1)

    def move_down(self, _action, _shortcut) -> None:
        """Move item down in hirarchy."""
        self._change_position(self.props.index + 1)

    def delete(self, _action, _shortcut) -> None:
        """Delete Item."""
        name = self.props.item.get_name()
        self.props.application.get_data().delete_items([self.props.item])
        toast = Adw.Toast.new(_("Deleted {name}").format(name=name))
        toast.set_button_label(_("Undo"))
        toast.set_action_name("app.undo")
        self.props.application.get_window().add_toast(toast)

    def edit(self, _action, _shortcut) -> None:
        """Show Edit Item Dialog."""
        EditItemDialog(self.props.application, self.props.item)
