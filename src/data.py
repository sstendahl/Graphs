# SPDX-License-Identifier: GPL-3.0-or-later
"""
Data management module.

Classes:
    Data
"""
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
        items-change: Items are added or removed
        items-ignored: Items are ignored during addition

    Functions:
        to_list
        set_from_list
        is_empty
        get_names
        change_position
        add_items
        delete_items
    """

    __gtype_name__ = "Data"
    __gsignals__ = {
        "items-change": (GObject.SIGNAL_RUN_FIRST, None, ()),
        "items-ignored": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    application = GObject.Property(type=object)

    def __init__(self, application):
        """Init the dataclass."""
        super().__init__(application=application)
        self._items = {}

    def to_list(self) -> list:
        """Get a list of all items in dict form."""
        return [item_.to_dict() for item_ in self]

    def set_from_list(self, items: list):
        """Set items from a list of items in dict form."""
        self.props.items = [item.new_from_dict(d) for d in items]

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
        return list(self._items.values())

    @items.setter
    def items(self, items: list):
        self._items = {item_.key: item_ for item_ in items}
        for item_ in items:
            self._connect_to_item(item_)
        self.emit("items-change")

    def get_names(self) -> list:
        """All items' names."""
        return [item_.name for item_ in self._items.values()]

    def __len__(self) -> int:
        """Amount of managed items."""
        return len(self._items)

    def __iter__(self):
        """Iterate over items."""
        return iter(self._items.values())

    def __getitem__(self, getter):
        """Get item by index or key."""
        if isinstance(getter, str):
            return self._items[getter]
        return list(self._items.values())[getter]

    def change_position(self, key1: str, key2: str):
        """Change key position of key2 to that of key1."""
        keys = list(self._items.keys())
        items = list(self._items.values())
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
        self.props.items = items

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
        figure_settings = self.props.application.props.figure_settings
        settings = self.props.application.props.settings
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
                    new_item.key = \
                        self.props.items[names.index(new_item.name)].key

            if new_item.xlabel:
                original_position = new_item.xposition
                if new_item.xposition == 0:
                    if _is_default("bottom-label"):
                        figure_settings.props.bottom_label = new_item.xlabel
                    elif new_item.xlabel != figure_settings.props.bottom_label:
                        new_item.xposition = 1
                if new_item.xposition == 1:
                    if _is_default("top-label"):
                        figure_settings.props.top_label = new_item.xlabel
                    elif new_item.xlabel != figure_settings.props.bottom_label:
                        new_item.xposition = original_position
            if new_item.ylabel:
                original_position = new_item.yposition
                if new_item.yposition == 0:
                    if _is_default("left-label"):
                        figure_settings.props.left_label = new_item.ylabel
                    elif new_item.ylabel != figure_settings.props.left_label:
                        new_item.yposition = 1
                if new_item.yposition == 1:
                    if _is_default("right-label"):
                        figure_settings.props.right_label = new_item.ylabel
                    elif new_item.ylabel != figure_settings.props.left_label:
                        new_item.yposition = original_position
            if new_item.color == "":
                new_item.color = utilities.get_next_color(
                    self._items.values(),
                )

            self._connect_to_item(new_item)
            self._items[new_item.key] = new_item
        utilities.optimize_limits(self.props.application)
        self.props.application.props.clipboard.add()
        if ignored:
            self.emit("items-ignored", ", ".join(ignored))
        self.emit("items-change")
        self.notify("items")
        self.notify("items_selected")

    def delete_items(self, items: list):
        """Delete specified items."""
        for i in items:
            del self._items[i.key]
        self.emit("items-change")
        self.notify("items")
        self.notify("items_selected")

    def _connect_to_item(self, item_):
        item_.connect(
            "notify::selected", lambda _x, _y: self.notify("items_selected"),
        )
        for prop in ["xposition", "yposition"]:
            item_.connect(f"notify::{prop}", self._on_item_position_change)

    def _on_item_position_change(self, _item, _ignored):
        utilities.optimize_limits(self.props.application)
        self.notify("items")
