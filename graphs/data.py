# SPDX-License-Identifier: GPL-3.0-or-later
"""Data management module."""
import logging
from collections.abc import Iterator
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs import project, utilities


class Data(Graphs.Data):
    """Class for managing data."""

    __gtype_name__ = "GraphsPythonData"

    def __init__(self):
        super().__init__()
        self.connect("load-request", self._on_load_request)

    def __len__(self) -> int:
        """Magic alias for `get_n_items()`."""
        return self.get_n_items()

    def __iter__(self) -> Iterator[Graphs.Item]:
        """Iterate over items."""
        for i in range(self.get_n_items()):
            yield self.get_item(i)

    def __getitem__(self, pos: int):
        """Magic alias for retrieving items."""
        return self.get_item(pos)

    @staticmethod
    def _serialize_history_state(state):
        changes = []
        for change in state.changes():
            if isinstance(change, Graphs.DataHistoryPropertyChange):
                new_change = (
                    change.index(),
                    change.prop(),
                    change.old_value().unpack(),
                    change.new_value().unpack(),
                )
                change_type = Graphs.ChangeType.ITEM_PROPERTY_CHANGED
            elif isinstance(change, Graphs.DataHistoryItemAdded):
                new_change = change.item().unpack()
                change_type = Graphs.ChangeType.ITEM_ADDED
            elif isinstance(change, Graphs.DataHistoryItemRemoved):
                new_change = (change.item().unpack(), change.index())
                change_type = Graphs.ChangeType.ITEM_REMOVED
            elif isinstance(change, Graphs.DataHistoryItemsSwapped):
                # This was swapped in previous implementations
                new_change = (change.index2(), change.index1())
                change_type = Graphs.ChangeType.ITEMS_SWAPPED
            elif isinstance(change, Graphs.DataHistoryFigureSettingsChange):
                new_change = (
                    change.prop(),
                    change.old_value().unpack(),
                    change.new_value().unpack(),
                )
                change_type = Graphs.ChangeType.FIGURE_SETTINGS_CHANGED
            changes.append((change_type, new_change))
        return changes, state.limits().values()

    def get_project_dict(self) -> dict:
        """Convert data to dict."""
        figure_settings = self.get_figure_settings()
        history_pos, history_states = self.get_data_history()
        view_pos, view_states = self.get_view_history()
        history_states = [
            self._serialize_history_state(state)
            for state in history_states
        ]
        return {
            "version": self.get_version(),
            "data": [item.to_variant(self.index).unpack() for item in self],
            "figure-settings": {
                key.replace("_", "-"): figure_settings.get_property(key)
                for key in dir(figure_settings.props)
            },
            "history-states": history_states,
            "history-position": history_pos,
            "view-history-states": [lims.values() for lims in view_states],
            "view-history-position": view_pos,
        }

    @staticmethod
    def _deserialize_history_state(state):
        changes = []
        for change_type, change in state[0]:
            match change_type:
                case Graphs.ChangeType.ITEM_PROPERTY_CHANGED:
                    index, prop, old_value, new_value = change
                    new_change = Graphs.DataHistoryPropertyChange.new(
                        index,
                        prop,
                        utilities.value_to_gvariant(old_value),
                        utilities.value_to_gvariant(new_value),
                    )
                case Graphs.ChangeType.ITEM_ADDED:
                    new_change = Graphs.DataHistoryItemAdded.new(
                        utilities.value_to_gvariant(change),
                    )
                case Graphs.ChangeType.ITEM_REMOVED:
                    item, index = change
                    new_change = Graphs.DataHistoryItemRemoved.new(
                        utilities.value_to_gvariant(item),
                        index,
                    )
                case Graphs.ChangeType.ITEMS_SWAPPED:
                    index2, index1 = change
                    new_change = Graphs.DataHistoryItemsSwapped.new(
                        index1,
                        index2,
                    )
                case Graphs.ChangeType.FIGURE_SETTINGS_CHANGED:
                    prop, old_value, new_value = change
                    new_change = Graphs.DataHistoryFigureSettingsChange.new(
                        prop,
                        utilities.value_to_gvariant(old_value),
                        utilities.value_to_gvariant(new_value),
                    )
            changes.append(new_change)
        limits = Graphs.Limits.new(state[1])
        return Graphs.DataHistoryState.new(limits, changes)

    def load_from_project_dict(self, project_dict: dict) -> None:
        """Load data from dict."""
        # Load data
        self.set_figure_settings(
            Graphs.FigureSettings(
                **{
                    key.replace("-", "_"): value
                    for (key, value) in project_dict["figure-settings"].items()
                },
            ),
        )
        data = [
            utilities.value_to_gvariant(item)
            for item in project_dict["data"]
        ]
        self.set_items(Graphs.items_from_variants(data))

        # Set clipboard
        history_states = [
            self._deserialize_history_state(state)
            for state in project_dict["history-states"]
        ]
        self.set_data_history(project_dict["history-position"], history_states)
        view_states = project_dict["view-history-states"]
        limits = list(map(Graphs.Limits.new, view_states))
        self.set_view_history(project_dict["view-history-position"], limits)

    def _save(self) -> None:
        project.save_project_dict(self.props.file, self.get_project_dict())

    @staticmethod
    def _on_load_request(
        self,
        file: Gio.File,
        parse_flags: Graphs.ProjectParseFlags,
    ) -> str:
        try:
            project_dict = project.read_project_file(file, parse_flags)
        except project.ProjectParseError as error:
            if error.log:
                logging.exception(error)
            return error.message
        current_data = self.get_project_dict()
        try:
            self.load_from_project_dict(project_dict)
        except Exception:
            self.load_from_project_dict(current_data)
            msg = _("Failed to load project")
            logging.exception(msg)
            return msg
        return ""
