# SPDX-License-Identifier: GPL-3.0-or-later
"""Data management module."""
import copy
import logging
from collections import OrderedDict
from collections.abc import Iterator
from gettext import gettext as _
from operator import itemgetter

from gi.repository import Gio, Graphs, Gtk

from graphs import misc, project
from graphs.item import ItemFactory

_FIGURE_SETTINGS_HISTORY_IGNORELIST = misc.LIMITS + [
    "min-selected",
    "max-selected",
]


class Data(Graphs.Data):
    """Class for managing data."""

    __gtype_name__ = "GraphsPythonData"

    def __init__(self):
        super().__init__()
        self.connect("load-request", self._on_load_request)
        self.connect("position-changed", self._on_position_changed)
        self.connect("item-changed", self._on_item_changed)
        self.connect("item-added", self._on_item_added)
        self.connect("item-removed", self._on_item_removed)
        self.connect(
            "figure-settings-changed",
            self._on_figure_settings_changed,
        )
        self.connect(
            "add-history-state-request",
            self._on_add_history_state_request,
        )
        self.connect("undo-request", self._on_undo_request)
        self.connect("redo-request", self._on_redo_request)

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

    def _item_dict(self, item: Graphs.Item) -> dict:
        """Convert an item to a dict."""
        dictionary = ItemFactory.to_dict(item)
        return ItemFactory.link_dependencies(item, dictionary, self)

    def _init_history_states(self) -> None:
        self.init_history_callback([])
        self._set_data_copy()

    @staticmethod
    def _on_position_changed(self, index1: int, index2: int) -> None:
        """Change item position of index2 to that of index1."""
        self._current_batch.append((
            Graphs.ChangeType.ITEMS_SWAPPED,
            (index2, index1),
        ))

    @staticmethod
    def _on_item_added(self, item: Graphs.Item) -> None:
        self._current_batch.append((
            Graphs.ChangeType.ITEM_ADDED,
            self._item_dict(item),
        ))

    @staticmethod
    def _on_item_removed(self, item: Graphs.Item, index: int) -> None:
        self._current_batch.append((
            Graphs.ChangeType.ITEM_REMOVED,
            (index, self._item_dict(item)),
        ))

    @staticmethod
    def _on_item_changed(self, item: Graphs.Item, prop: str) -> None:
        index = self.index(item)
        self._current_batch.append((
            Graphs.ChangeType.ITEM_PROPERTY_CHANGED,
            (
                index,
                prop,
                copy.deepcopy(self._data_copy[index][prop]),
                ItemFactory.serialize_property(item, prop),
            ),
        ))

    @staticmethod
    def _on_figure_settings_changed(self, prop: str) -> None:
        if prop in _FIGURE_SETTINGS_HISTORY_IGNORELIST:
            return
        self._current_batch.append((
            Graphs.ChangeType.FIGURE_SETTINGS_CHANGED,
            (
                prop,
                copy.deepcopy(self._figure_settings_copy[prop]),
                copy.deepcopy(self.props.figure_settings.get_property(prop)),
            ),
        ))

    def _set_data_copy(self) -> None:
        """Set a deep copy for the data."""
        self._current_batch: list = []
        self._data_copy = copy.deepcopy(
            [ItemFactory.to_dict(item) for item in self],
        )
        self._figure_settings_copy = copy.deepcopy({
            prop.replace("_", "-"):
            self.props.figure_settings.get_property(prop)
            for prop in dir(self.props.figure_settings.props)
        })

    def _collapse_current_batch(self) -> None:
        """
        Collapse transitive changes within the current history batch.

        This method reduces redundant "change" entries in the current history
        batch:
        - Multiple consecutive item and figure settings changes to the same
          property are collapsed into a single change.
        - If a collapsed change would be meaningless (the original old value
          is equal to the most recent new value), that change is dropped.
        - If the batch contains structural changes like items added or removed,
          the method aborts and leaves the batch unchanged.
        """
        if not self._current_batch:
            # Nothing to collapse
            return

        collapsed = OrderedDict()

        for change_type, data in self._current_batch:
            match change_type:
                case Graphs.ChangeType.ITEM_PROPERTY_CHANGED:
                    index, prop, _old_value, new_value = data
                    key = (change_type, index, prop)

                    if key not in collapsed:
                        collapsed[key] = (change_type, data)
                    else:
                        first_old = collapsed[key][1][2]
                        if first_old == new_value:
                            collapsed.pop(key)
                        else:
                            collapsed[key] = (
                                Graphs.ChangeType.ITEM_PROPERTY_CHANGED,
                                (index, prop, first_old, new_value),
                            )

                case Graphs.ChangeType.FIGURE_SETTINGS_CHANGED:
                    prop, _old_value, new_value = data
                    key = (change_type, prop)

                    if key not in collapsed:
                        collapsed[key] = (change_type, data)
                    else:
                        first_old = collapsed[key][1][1]
                        if first_old == new_value:
                            collapsed.pop(key)
                        else:
                            collapsed[key] = (
                                Graphs.ChangeType.FIGURE_SETTINGS_CHANGED,
                                (prop, first_old, new_value),
                            )

                case _:
                    # On any other change such as items added or removed we
                    # abort collapsing
                    return

        self._current_batch = list(collapsed.values())

    @staticmethod
    def _on_add_history_state_request(self) -> bool:
        """Add a state to the clipboard."""
        self._collapse_current_batch()
        if not self._current_batch:
            # Nothing to add
            return False

        self.add_history_state_callback(self._current_batch)
        self._current_batch = []
        return True

    @staticmethod
    def _on_undo_request(self, batch) -> None:
        """Undo the latest change that was added to the clipboard."""
        selected = Gtk.Bitset.new_empty()
        mask = Gtk.Bitset.new_empty()
        for change_type, change in reversed(batch):
            match change_type:
                case Graphs.ChangeType.ITEM_PROPERTY_CHANGED:
                    index, prop, value = itemgetter(0, 1, 2)(change)
                    if prop == "selected":
                        mask.add(index)
                        if value:
                            selected.add(index)
                    else:
                        ItemFactory.deserialize_property(
                            self[index],
                            prop,
                            value,
                        )
                case Graphs.ChangeType.ITEM_ADDED:
                    self._remove_item(self.get_n_items() - 1)
                case Graphs.ChangeType.ITEM_REMOVED:
                    dictionary = copy.deepcopy(change[1])
                    item = ItemFactory.new_from_dict(dictionary)
                    items = list(self)
                    items.insert(change[0], item)
                    ItemFactory.resolve_dependencies(item, dictionary, items)
                    self._insert_item(item, change[0])
                case Graphs.ChangeType.ITEMS_SWAPPED:
                    self.change_position(change[0], change[1])
                case Graphs.ChangeType.FIGURE_SETTINGS_CHANGED:
                    self.props.figure_settings.set_property(
                        change[0],
                        change[1],
                    )
        self.set_selection(selected, mask)
        self._set_data_copy()

    @staticmethod
    def _on_redo_request(self, batch) -> None:
        """Redo the latest change that was added to the clipboard."""
        selected = Gtk.Bitset.new_empty()
        mask = Gtk.Bitset.new_empty()
        for change_type, change in batch:
            match change_type:
                case Graphs.ChangeType.ITEM_PROPERTY_CHANGED:
                    index, prop, value = itemgetter(0, 1, 3)(change)
                    if prop == "selected":
                        mask.add(index)
                        if value:
                            selected.add(index)
                    else:
                        ItemFactory.deserialize_property(
                            self[index],
                            prop,
                            value,
                        )
                case Graphs.ChangeType.ITEM_ADDED:
                    dictionary = copy.deepcopy(change)
                    item = ItemFactory.new_from_dict(dictionary)
                    items = list(self) + [item]
                    ItemFactory.resolve_dependencies(item, dictionary, items)
                    self._add_item(item)
                case Graphs.ChangeType.ITEM_REMOVED:
                    self._remove_item(change[0])
                case Graphs.ChangeType.ITEMS_SWAPPED:
                    self.change_position(change[1], change[0])
                case Graphs.ChangeType.FIGURE_SETTINGS_CHANGED:
                    self.props.figure_settings.set_property(
                        change[0],
                        change[2],
                    )
        self.set_selection(selected, mask)
        self._set_data_copy()

    def get_project_dict(self) -> dict:
        """Convert data to dict."""
        figure_settings = self.get_figure_settings()
        view_pos, view_states = self.get_view_history()
        history_pos, limits, batches = self.get_data_history()
        return {
            "version": self.get_version(),
            "data": [self._item_dict(item) for item in self],
            "figure-settings": {
                key.replace("_", "-"): figure_settings.get_property(key)
                for key in dir(figure_settings.props)
            },
            "history-states": [
                (batch, lims.values())
                for batch, lims in zip(batches, limits)
            ],
            "history-position": history_pos,
            "view-history-states": [lims.values() for lims in view_states],
            "view-history-position": view_pos,
        }

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
        dictionaries = project_dict["data"]
        items = list(map(ItemFactory.new_from_dict, dictionaries))
        for item, dictionary in zip(items, dictionaries):
            ItemFactory.resolve_dependencies(item, dictionary, items)
        self.set_items(items)

        # Set clipboard
        self._set_data_copy()
        history_states = {
            Graphs.Limits.new(lims): batch
            for batch, lims in project_dict["history-states"]
        }
        self.set_data_history(
            project_dict["history-position"],
            list(history_states.keys()),
            list(history_states.values()),
        )
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
