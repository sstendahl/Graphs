# SPDX-License-Identifier: GPL-3.0-or-later
"""
Data management module.

Classes:
    Data
"""
import copy

from gi.repository import GObject, Graphs

from graphs import item, utilities

from matplotlib import pyplot


class Data(GObject.Object, Graphs.DataInterface):
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
        change_position
        add_items
        delete_items
    """

    __gtype_name__ = "GraphsData"
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
        return [item.to_dict(item_) for item_ in self]

    def to_dict(self) -> dict:
        """Get a dictionary of all items sorted by their key"""
        return {item_.get_uuid(): item.to_dict(item_) for item_ in self}

    def set_from_list(self, items: list):
        """Set items from a list of items in dict form."""
        self.set_items([item.new_from_dict(d) for d in items])

    def is_empty(self) -> bool:
        """Whether or not the class is empty."""
        return not self._items

    @GObject.Property(type=bool, default=False, flags=1)
    def items_selected(self) -> bool:
        """Whether or not at least one item is selected."""
        return any(item_.get_selected() for item_ in self)

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

    def set_items(self, items: list):
        """Set all managed items."""
        for item_ in items:
            self.append(item_)
        self._items = {item_.get_uuid(): item_ for item_ in items}

    def append(self, item_):
        """Append items to self."""
        self._connect_to_item(item_)
        self._items[item_.get_uuid()] = item_
        self.notify("items")

    def pop(self, key):
        """Pop and delete item."""
        item_ = self._items[key]
        self._items.pop(key)
        del item_
        self.notify("items")

    def index(self, item_):
        """Get the index of an item."""
        return self.get_items().index(item_)

    def get_names(self) -> list:
        """All items' names."""
        return [item_.get_name() for item_ in self]

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

    def change_position(self, index1: int, index2: int):
        """Change item position of index2 to that of index1."""
        items = self.get_items()
        # Check if target key is lower in the order, if so we can put the old
        # key below the target key. Otherwise put it above.
        if index1 < index2:
            items[index1:index2 + 1] = [items[index2]] + items[index1:index2]
        else:
            items[index2:index1 + 1] = \
                items[index2 + 1:index1 + 1] + [items[index2]]
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
        application = self.get_application()
        figure_settings = application.get_figure_settings()
        settings = application.get_settings()
        clipboard = application.get_clipboard()
        handle_duplicates = \
            settings.get_child("general").get_enum("handle-duplicates")
        color_cycle = pyplot.rcParams["axes.prop_cycle"].by_key()["color"]
        used_colors = []

        def _append_used_color(color):
            used_colors.append(color)
            # If we've got all colors once, remove those from used_colors so we
            # can loop around
            if set(used_colors) == set(color_cycle):
                for color in color_cycle:
                    used_colors.remove(color)

        for item_ in self:
            _append_used_color(item_.get_color())

        def _is_default(prop):
            return figure_settings.get_property(prop) == \
                settings.get_child("figure").get_string(prop)

        for new_item in items:
            names = self.get_names()
            if new_item.get_name() in names:
                if handle_duplicates == 0:  # Auto-add
                    i = 1
                    while True:
                        new_name = f"{new_item.get_name()} ({i})"
                        if new_name not in names:
                            break
                        i += 1
                    new_item.set_name(new_name)
                elif handle_duplicates == 1:  # Ignore
                    ignored.append(new_item.get_name())
                    continue
                elif handle_duplicates == 3:  # Override
                    index = names.index(new_item.get_name())
                    existing_item = self[index]
                    clipboard.append(
                        (2, (index, existing_item.to_dict(item_))),
                    )
                    new_item.set_uuid(existing_item.get_uuid())

            xlabel = new_item.get_xlabel()
            if xlabel:
                original_position = new_item.get_xposition()
                if original_position == 0:
                    if _is_default("bottom-label"):
                        figure_settings.set_bottom_label(xlabel)
                    elif xlabel != figure_settings.get_bottom_label():
                        new_item.set_xposition(1)
                if new_item.get_xposition() == 1:
                    if _is_default("top-label"):
                        figure_settings.set_top_label(xlabel)
                    elif xlabel != figure_settings.get_top_label():
                        new_item.set_xposition(original_position)
            ylabel = new_item.get_ylabel()
            if ylabel:
                original_position = new_item.get_yposition()
                if original_position == 0:
                    if _is_default("left-label"):
                        figure_settings.set_left_label(ylabel)
                    elif ylabel != figure_settings.get_left_label():
                        new_item.set_yposition(1)
                if new_item.get_yposition() == 1:
                    if _is_default("right-label"):
                        figure_settings.set_right_label(ylabel)
                    elif ylabel != figure_settings.get_right_label():
                        new_item.set_yposition(original_position)
            if new_item.get_color() == "":
                for color in color_cycle:
                    if color not in used_colors:
                        new_item.set_color(color)
                        _append_used_color(color)
                        break

            self.append(new_item)
            clipboard.append((1, copy.deepcopy(item.to_dict(new_item))))
        utilities.optimize_limits(application)
        clipboard.add()
        if ignored:
            self.emit("items-ignored", ", ".join(ignored))
        self.notify("items")
        self.notify("items_selected")

    def add_unconnected_items(self, items: list):
        """
        Adds items without connecting any handles

        Useful for data sets which work in complete isolation from the
        main application, and should not be copied into a clipboard.
        """
        for new_item in items:
            self._items[new_item.uuid] = new_item

    def delete_items(self, items: list):
        """Delete specified items."""
        for item_ in items:
            self.get_application().get_clipboard().append(
                (2, (self.index(item_), item.to_dict(item_))),
            )
            self.pop(item_.get_uuid())
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
