# SPDX-License-Identifier: GPL-3.0-or-later
"""
Data management module.

Classes:
    Data
"""
import copy

from gi.repository import GObject, Graphs

from graphs import item, ui, utilities

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
    figure_settings = GObject.Property(type=Graphs.FigureSettings)
    history_states = GObject.Property(type=object)
    history_pos = GObject.Property(type=int, default=-1)
    current_batch = GObject.Property(type=object)
    data_copy = GObject.Property(type=object)

    def __init__(self, application, settings):
        """Init the dataclass."""
        figure_settings = Graphs.FigureSettings.new(
            settings.get_child("figure"),
        )
        super().__init__(
            application=application, figure_settings=figure_settings,
            current_batch=[], data_copy={},
            history_states=[([], figure_settings.get_limits())],
        )
        self._items = {}

    def get_application(self):
        """Get application property."""
        return self.props.application

    def get_figure_settings(self):
        """Get figure settings property."""
        return self.props.figure_settings

    def to_list(self) -> list:
        """Get a list of all items in dict form."""
        return [item.to_dict(item_) for item_ in self]

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
        self.props.current_batch.append((3, (index2, index1)))

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
        figure_settings = self.get_figure_settings()
        settings = application.get_settings()
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
                    self.props.current_batch.append(
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
            self.props.current_batch.append(
                (1, copy.deepcopy(item.to_dict(new_item))),
            )
        utilities.optimize_limits(application)
        self.add_history_state()
        if ignored:
            self.emit("items-ignored", ", ".join(ignored))
        self.notify("items")
        self.notify("items_selected")

    def delete_items(self, items: list):
        """Delete specified items."""
        for item_ in items:
            self.props.current_batch.append(
                (2, (self.index(item_), item.to_dict(item_))),
            )
            self.pop(item_.get_uuid())
        self.add_history_state()
        self.notify("items_selected")

    def _connect_to_item(self, item_):
        item_.connect("notify::selected", self._on_item_select)
        item_.connect("notify", self._on_item_change)
        for prop in ["xposition", "yposition"]:
            item_.connect(f"notify::{prop}", self._on_item_position_change)

    def _on_item_position_change(self, _item, _ignored):
        utilities.optimize_limits(self.get_application())
        self.notify("items")

    def _on_item_select(self, _x, _y):
        self.notify("items_selected")
        if self.get_application().get_settings(
                "general").get_boolean("hide-unselected"):
            self.notify("items")

    def _on_item_change(self, item_, param):
        self.props.current_batch.append((0, (
            item_.get_uuid(), param.name,
            copy.deepcopy(self.props.data_copy[item_.get_uuid()][param.name]),
            copy.deepcopy(item_.get_property(param.name)),
        )))

    def _set_data_copy(self):
        self.props.current_batch = []
        self.props.data_copy = copy.deepcopy(
            {item_.get_uuid(): item.to_dict(item_) for item_ in self},
        )

    def add_history_state(self, old_limits=None):
        if not self.props.current_batch:
            return
        if self.props.history_pos != -1:
            self.props.history_states = \
                self.props.history_states[:self.props.history_pos + 1]
        self.props.history_pos = -1
        self.props.history_states.append((
            self.props.current_batch,
            self.get_figure_settings().get_limits(),
        ))
        ui.set_clipboard_buttons(self.get_application())

        if old_limits is not None:
            for index in range(8):
                self.props.history_states[
                    self.props.history_pos - 1][1][index] = old_limits[index]
        # Keep history srares length limited to 100 spots
        if len(self.props.history_states) > 101:
            self.props.history_states = self.props.history_states[1:]
        self._set_data_copy()

    def undo(self):
        if abs(self.props.history_pos) < len(self.props.history_states):
            batch = self.props.history_states[self.props.history_pos][0]
            self.props.history_pos -= 1
            items_changed = False
            for change_type, change in reversed(batch):
                if change_type == 0:
                    self[change[0]].set_property(change[1], change[2])
                elif change_type == 1:
                    self.pop(change["uuid"])
                    items_changed = True
                elif change_type == 2:
                    item_ = item.new_from_dict(change[1])
                    self.append(item_)
                    self.change_position(change[0], len(self))
                    items_changed = True
                elif change_type == 3:
                    self.change_position(change[0], change[1])
                    items_changed = True
            if items_changed:
                self.notify("items")
            self.notify("items_selected")
            self.get_figure_settings().set_limits(
                self.props.history_states[self.props.history_pos][1],
            )
            ui.set_clipboard_buttons(self.get_application())
            self._set_data_copy()
            self.get_application().get_view_clipboard().add()

    def redo(self):
        if self.props.history_pos < -1:
            self.props.history_pos += 1
            state = self.props.history_states[self.props.history_pos]
            items_changed = False
            for change_type, change in state[0]:
                if change_type == 0:
                    self[change[0]].set_property(change[1], change[3])
                elif change_type == 1:
                    self.append(item.new_from_dict(change))
                    items_changed = True
                elif change_type == 2:
                    self.pop(change[1]["uuid"])
                    items_changed = True
                elif change_type == 3:
                    self.change_position(change[1], change[0])
                    items_changed = True
            if items_changed:
                self.notify("items")
            self.notify("items_selected")
            self.get_figure_settings().set_limits(state[1])
            ui.set_clipboard_buttons(self.get_application())
            self._set_data_copy()
            self.get_application().get_view_clipboard().add()
