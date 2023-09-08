# SPDX-License-Identifier: GPL-3.0-or-later
"""
Data management module.

Classes:
    Data
"""
import copy

from gi.repository import GObject

from graphs import item, utilities


class Data(GObject.Object):
    """
    Class for managing data.

    Properties:
        application
        items-selected
        items

    Signals:
        items-ignored: Items are ignored during addition

    Functions:
        get_application
        to_list
        to_dict
        set_from_list
        is_empty
        get_items
        set_items
        append
        pop
        index
        get_names
        get_keys
        change_position
        add_items
        delete_items
    """

    __gtype_name__ = "Data"
    __gsignals__ = {
        "items-ignored": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    application = GObject.Property(type=object)

    def __init__(self, application):
        """Init the dataclass."""
        super().__init__(application=application)
        self._items = {}

    def get_application(self):
        """Get application property."""
        return self.props.application

    def to_list(self) -> list:
        """Get a list of all items in dict form."""
        return [item_.to_dict() for item_ in self]

    def to_dict(self) -> dict:
        """Get a dictionary of all items sorted by their key"""
        return {item_.key: item_.to_dict() for item_ in self}

    def set_from_list(self, items: list):
        """Set items from a list of items in dict form."""
        self.set_items([item.new_from_dict(d) for d in items])

    def is_empty(self) -> bool:
        """Whether or not the class is empty."""
        return not self._items

    @GObject.Property(type=bool, default=False, flags=1)
    def items_selected(self) -> bool:
        """Whether or not at least one item is selected."""
        return any(item_.selected for item_ in self)

    @GObject.Property
    def items(self) -> list:
        """All managed items."""
        return self.get_items()

    @items.setter
    def items(self, items: list):
        self.set_items(items)

    def get_items(self) -> list:
        """Get all managed items."""
        return list(self._items.values())

    def get_item_by_index(self, index: int):
        """Get item given an index."""
        return list(self._items.values())[index]

    def set_items(self, items: list):
        """Set all managed items."""
        for item_ in items:
            self.append(item_)
        self._items = {item_.key: item_ for item_ in items}

    def append(self, item_):
        """Append items to self."""
        self._connect_to_item(item_)
        self._items[item_.key] = item_
        self.notify("items")

    def pop(self, key):
        """Pop and delete item."""
        item_ = self._items[key]
        self._items.pop(key)
        del item_
        self.notify("items")

    def index(self, key):
        """Get the indexs of key."""
        return self.get_keys().index(key)

    def get_names(self) -> list:
        """All items' names."""
        return [item_.name for item_ in self]

    def get_keys(self) -> list:
        """All item's keys."""
        return list(self._items.keys())

    def __len__(self) -> int:
        """Amount of managed items."""
        return len(self._items)

    def __iter__(self):
        """Iterate over items."""
        return iter(self.get_items())

    def __getitem__(self, getter):
        """Get item by index or key."""
        if isinstance(getter, str):
            return self._items[getter]
        return self.get_items()[getter]

    def change_position(self, key1: str, key2: str):
        """Change key position of key2 to that of key1."""
        keys = self.get_keys()
        items = self.get_items()
        index1 = keys.index(key2)
        index2 = keys.index(key1)
        # Check if target key is lower in the order, if so we can put the old
        # key below the target key. Otherwise put it above.
        if index1 < index2:
            items[index1:index2 + 1] = items[index1 + 1:index2 + 1] + \
                [self._items[key2]]
        else:
            items[index2:index1 + 1] = \
                [self._items[key2]] + items[index2:index1]
        self.items = items

    def add_items(self, items: list):
        """
        Add items to be managed.

        Respects settings in regards to handling duplicate names.
        New Items with a x- or y-label change the figures current labels if
        they are still the default. If they are already modified and do not
        match the items label, they get moved to another axis.
        If items are ignored, the `items-ignored` signal will be emmitted.
        """
        ignored = []
        figure_settings = self.get_application().get_figure_settings()
        settings = self.get_application().props.settings
        handle_duplicates = \
            settings.get_child("general").get_enum("handle-duplicates")

        def _is_default(prop):
            return figure_settings.get_property(prop) == \
                settings.get_child("figure").get_string(prop)

        for new_item in items:
            names = self.get_names()
            if new_item.name in names:
                if handle_duplicates == 0:  # Auto-add
                    i = 1
                    while True:
                        new_name = f"{new_item.name} ({i})"
                        if new_name not in names:
                            break
                        i += 1
                    new_item.name = new_name
                elif handle_duplicates == 1:  # Ignore
                    ignored.append(new_item.name)
                    continue
                elif handle_duplicates == 3:  # Override
                    new_item.key = self[names.index(new_item.name)].key

            if new_item.xlabel:
                original_position = new_item.xposition
                if new_item.xposition == 0:
                    if _is_default("bottom-label"):
                        figure_settings.set_bottom_label(new_item.xlabel)
                    elif new_item.xlabel != figure_settings.get_bottom_label():
                        new_item.xposition = 1
                if new_item.xposition == 1:
                    if _is_default("top-label"):
                        figure_settings.set_top_label(new_item.xlabel)
                    elif new_item.xlabel != figure_settings.get_top_label():
                        new_item.xposition = original_position
            if new_item.ylabel:
                original_position = new_item.yposition
                if new_item.yposition == 0:
                    if _is_default("left-label"):
                        figure_settings.set_left_label(new_item.ylabel)
                    elif new_item.ylabel != figure_settings.get_left_label():
                        new_item.yposition = 1
                if new_item.yposition == 1:
                    if _is_default("right-label"):
                        figure_settings.set_right_label(new_item.ylabel)
                    elif new_item.ylabel != figure_settings.get_right_label():
                        new_item.yposition = original_position
            if new_item.color == "":
                new_item.color = utilities.get_next_color(self.get_items())

            self.append(new_item)
            self.get_application().get_clipboard().append(
                (1, copy.deepcopy(new_item.to_dict())),
            )
        utilities.optimize_limits(self.get_application())
        self.get_application().get_clipboard().add()
        if ignored:
            self.emit("items-ignored", ", ".join(ignored))
        self.notify("items")
        self.notify("items_selected")

    def delete_items(self, items: list):
        """Delete specified items."""
        for item_ in items:
            self.get_application().get_clipboard().append(
                (2, (self.index(item_.key), item_.to_dict())),
            )
            self.pop(item_.key)
        self.get_application().get_clipboard().add()
        self.notify("items_selected")

    def _connect_to_item(self, item_):
        item_.connect(
            "notify::selected", lambda _x, _y: self.notify("items_selected"),
        )
        item_.connect(
            "notify", self.get_application().get_clipboard().on_item_change,
        )
        for prop in ["xposition", "yposition"]:
            item_.connect(f"notify::{prop}", self._on_item_position_change)

    def _on_item_position_change(self, _item, _ignored):
        utilities.optimize_limits(self.get_application())
        self.notify("items")
