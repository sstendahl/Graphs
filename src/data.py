# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import GObject

from graphs import item, plotting_tools


class Data(GObject.Object):
    __gtype_name__ = "Data"
    __gsignals__ = {
        "items-change": (GObject.SIGNAL_RUN_FIRST, None, ()),
        "items-ignored": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    application = GObject.Property(type=object)

    def __init__(self, application):
        super().__init__(application=application)
        self._items = {}

    def to_list(self) -> list:
        return [i.to_dict() for i in self._items.values()]

    def set_from_list(self, items: list):
        self.props.items = [item.new_from_dict(d) for d in items]

    def is_empty(self) -> bool:
        return not self._items

    @GObject.Property
    def items(self) -> list:
        return list(self._items.values())

    @items.setter
    def items(self, items: list):
        self._items = {item.key: item for item in items}
        self.emit("items-change")

    @GObject.Property
    def names(self) -> list:
        return [item.name for item in self._items.values()]

    @GObject.Property
    def keys(self) -> list:
        return list(self._items.keys())

    def __len__(self) -> int:
        return len(self._items)

    def add_items(self, items: list) -> list:
        ignored = []
        figure_settings = self.props.application.props.figure_settings
        settings = self.props.application.props.settings
        handle_duplicates = \
            settings.get_child("general").get_enum("handle-duplicates")

        def _is_default(prop):
            return figure_settings.get_property(prop) == \
                settings.get_child("figure").get_string(prop)

        for new_item in items:
            names = self.props.names
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
                if new_item.xposition == "bottom":
                    if _is_default("bottom-label"):
                        figure_settings.props.bottom_label = new_item.xlabel
                    elif new_item.xlabel != figure_settings.props.bottom_label:
                        new_item.xposition = "top"
                if new_item.xposition == "top":
                    if _is_default("top-label"):
                        figure_settings.props.top_label = new_item.xlabel
                    elif new_item.xlabel != figure_settings.props.bottom_label:
                        new_item.xposition = original_position
            if new_item.ylabel:
                original_position = new_item.yposition
                if new_item.yposition == "left":
                    if _is_default("left-label"):
                        figure_settings.props.left_label = new_item.ylabel
                    elif new_item.ylabel != figure_settings.props.left_label:
                        new_item.yposition = "right"
                if new_item.yposition == "right":
                    if _is_default("right-label"):
                        figure_settings.props.right_label = new_item.ylabel
                    elif new_item.ylabel != figure_settings.props.left_label:
                        new_item.yposition = original_position
            if new_item.color == "":
                new_item.color = \
                    plotting_tools.get_next_color(self.props.application)

            self._items[new_item.key] = new_item
        plotting_tools.optimize_limits(self.props.application)
        self.props.application.props.clipboard.add()
        if ignored:
            self.emit("items-ignored", ", ".join(ignored))
        self.emit("items-change")

    def delete_items(self, items):
        for i in items:
            del self._items[i.key]
        self.emit("items-change")
