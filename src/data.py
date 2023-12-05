# SPDX-License-Identifier: GPL-3.0-or-later
"""
Data management module.

Classes:
    Data
"""
import copy
import math
import os

from typing import Any
from pathlib import Path
from urllib.parse import urlparse

from gi.repository import GObject, Graphs

from graphs import item, misc, utilities

import numpy


_FIGURE_SETTINGS_HISTORY_IGNORELIST = misc.LIMITS + [
    "min_selected", "max_selected",
]


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
        get_items
        set_items
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
    can_undo = GObject.Property(type=bool, default=False)
    can_redo = GObject.Property(type=bool, default=False)
    can_view_back = GObject.Property(type=bool, default=False)
    can_view_forward = GObject.Property(type=bool, default=False)

    def __init__(self, application, settings):
        """Init the dataclass."""
        figure_settings = Graphs.FigureSettings.new(
            settings.get_child("figure"),
        )
        super().__init__(
            application=application, figure_settings=figure_settings,
        )
        limits = figure_settings.get_limits()
        self._history_states = [([], limits)]
        self._history_pos = -1
        self._view_history_states = [limits]
        self._view_history_pos = -1
        self._items = {}
        self._set_data_copy()
        self._unsaved = False
        self._project_uri = ""
        figure_settings.connect("notify", self._on_figure_settings_change)

    def get_application(self) -> Graphs.Application:
        """Get application property."""
        return self.props.application

    def get_figure_settings(self) -> Graphs.FigureSettings:
        """Get figure settings property."""
        return self.props.figure_settings

    @GObject.Property(type=bool, default=True, flags=1 | 1073741824)
    def empty(self) -> bool:
        """Whether or not the class is empty."""
        return not self._items

    @GObject.Property(type=bool, default=True)
    def unsaved(self) -> bool:
        """Whether or not the class is empty."""
        return self._unsaved

    @unsaved.setter
    def unsaved(self, unsaved):
        self._unsaved = unsaved

    @GObject.Property(type=str, default="")
    def project_uri(self) -> str:
        """Whether or not the class is empty."""
        return self._project_uri

    @project_uri.setter
    def project_uri(self, project_uri):
        self._project_uri = project_uri

    @GObject.Property(type=bool, default=False, flags=1)
    def items_selected(self) -> bool:
        """Whether or not at least one item is selected."""
        return any(item_.get_selected() for item_ in self)

    @GObject.Property(type=object, flags=3 | 1073741824)  # explicit notify
    def items(self) -> misc.ItemList:
        """All managed items."""
        return self.get_items()

    @items.setter
    def items(self, items: misc.ItemList) -> None:
        self.set_items(items)

    def get_items(self) -> misc.ItemList:
        """Get all managed items."""
        return list(self._items.values())

    def set_items(self, items: misc.ItemList) -> None:
        """Set all managed items."""
        self._items = {}
        for item_ in items:
            self._add_item(item_)
        self.notify("items")
        self.notify("empty")

    def _add_item(self, item_: Graphs.Item) -> None:
        """Append items to self."""
        self._connect_to_item(item_)
        self._items[item_.get_uuid()] = item_

    def _delete_item(self, uuid: str) -> None:
        """Pop and delete item."""
        item_ = self._items[uuid]
        self._items.pop(uuid)
        del item_

    def index(self, item_: Graphs.Item) -> int:
        """Get the index of an item."""
        return list(self._items.keys()).index(item_.get_uuid())

    def get_names(self) -> list[str]:
        """All items' names."""
        return [item_.get_name() for item_ in self]

    def get_n_items(self) -> int:
        """Amount of managed items."""
        return len(self._items)

    def get_at_pos(self, position: int) -> Graphs.Item:
        """Get item at position."""
        return self.get_items()[position]

    def get_for_uuid(self, uuid: str) -> Graphs.Item:
        """Get item for key."""
        return self._items[uuid]

    def __len__(self) -> int:
        """Magic alias for `get_n_items()`"""
        return self.get_n_items()

    def __iter__(self):
        """Iterate over items."""
        return iter(self._items.values())

    def __getitem__(self, getter: str | int):
        """Magic alias for retrieving items."""
        if isinstance(getter, str):
            return self.get_for_uuid(getter)
        return self.get_at_pos(getter)

    def change_position(self, index1: int, index2: int) -> None:
        """Change item position of index2 to that of index1."""
        items = self.get_items()
        # Check if target key is lower in the order, if so we can put the old
        # key below the target key. Otherwise put it above.
        if index1 < index2:
            items[index1:index2 + 1] = [items[index2]] + items[index1:index2]
        else:
            items[index2:index1 + 1] = \
                items[index2 + 1:index1 + 1] + [items[index2]]
        self.set_items(items)
        self._current_batch.append((3, (index2, index1)))

    def add_items(self, items: misc.ItemList) -> None:
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
        settings = application.get_settings_child("figure")
        style_manager = self.get_application().get_figure_style_manager()
        selected_style = style_manager.get_selected_style_params()
        color_cycle = selected_style["axes.prop_cycle"].by_key()["color"]
        used_colors = []

        def _append_used_color(color):
            if len(set(used_colors)) == len(color_cycle):
                for color in color_cycle:
                    used_colors.remove(color)
            used_colors.append(color)

        def _is_default(prop):
            return figure_settings.get_property(prop) == \
                settings.get_string(prop)

        for item_ in self:
            color = item_.get_color()
            if color in color_cycle:
                _append_used_color(color)
        used_names = set(self.get_names())
        for new_item in items:
            item_name = new_item.get_name()
            if item_name in used_names:
                new_item.set_name(utilities.get_duplicate_string(
                    item_name, used_names,
                ))
            used_names.add(new_item.get_name())
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
                        _append_used_color(color)
                        new_item.set_color(color)
                        break

            self._add_item(new_item)
            self._current_batch.append(
                (1, copy.deepcopy(new_item.to_dict())),
            )
        self.optimize_limits()
        self.add_history_state()
        if ignored:
            self.emit("items-ignored", ", ".join(ignored))
        self.notify("items")
        self.notify("items_selected")
        self.notify("empty")

    def delete_items(self, items: misc.ItemList):
        """Delete specified items."""
        for item_ in items:
            self._current_batch.append(
                (2, (self.index(item_), item_.to_dict())),
            )
            self._delete_item(item_.get_uuid())
        self.notify("items")
        self.add_history_state()
        self.notify("items_selected")
        self.notify("empty")

    def _connect_to_item(self, item_: Graphs.Item):
        item_.connect("notify::selected", self._on_item_select)
        item_.connect("notify", self._on_item_change)
        for prop in ("xposition", "yposition"):
            item_.connect(f"notify::{prop}", self._on_item_position_change)

    def _on_item_position_change(self, _item, _ignored) -> None:
        self.optimize_limits()
        self.notify("items")

    def _on_item_select(self, _x, _y) -> None:
        self.notify("items_selected")

    def _on_item_change(self, item_, param) -> None:
        self._current_batch.append((0, (
            item_.get_uuid(), param.name,
            copy.deepcopy(self._data_copy[item_.get_uuid()][param.name]),
            copy.deepcopy(item_.get_property(param.name)),
        )))
        self.change_unsaved(True)

    def _on_figure_settings_change(self, figure_settings, param) -> None:
        if param.name in _FIGURE_SETTINGS_HISTORY_IGNORELIST:
            return
        self._current_batch.append((4, (
            param.name,
            copy.deepcopy(self._figure_settings_copy[param.name]),
            copy.deepcopy(figure_settings.get_property(param.name)),
        )))

    def _set_data_copy(self) -> None:
        self._current_batch: list = []
        self._data_copy = copy.deepcopy(
            {item_.get_uuid(): item_.to_dict() for item_ in self},
        )
        self._figure_settings_copy = copy.deepcopy({
            prop.replace("_", "-"):
            self.props.figure_settings.get_property(prop)
            for prop in dir(self.props.figure_settings.props)
        })

    def add_history_state(self, old_limits: misc.Limits = None) -> None:
        if not self._current_batch:
            return
        if self._history_pos != -1:
            self._history_states = self._history_states[:self._history_pos + 1]
        self._history_pos = -1
        self._history_states.append(
            (self._current_batch, self.get_figure_settings().get_limits()),
        )
        if old_limits is not None:
            old_state = self._history_states[-2][1]
            for index in range(8):
                old_state[index] = old_limits[index]
        self.props.can_redo = False
        self.props.can_undo = True
        # Keep history states length limited to 100 spots
        if len(self._history_states) > 101:
            self._history_states = self._history_states[1:]
        self._set_data_copy()

    def undo(self) -> None:
        if not self.props.can_undo:
            return
        batch = self._history_states[self._history_pos][0]
        self._history_pos -= 1
        items_changed = False
        for change_type, change in reversed(batch):
            if change_type == 0:
                self[change[0]].set_property(change[1], change[2])
            elif change_type == 1:
                self._delete_item(change["uuid"])
                items_changed = True
            elif change_type == 2:
                item_ = item.new_from_dict(copy.deepcopy(change[1]))
                self._add_item(item_)
                self.change_position(change[0], len(self) - 1)
                items_changed = True
            elif change_type == 3:
                self.change_position(change[0], change[1])
                items_changed = True
            elif change_type == 4:
                self.props.figure_settings.set_property(
                    change[0], change[1],
                )
        if items_changed:
            self.notify("items")
            self.notify("empty")
        self.notify("items_selected")
        self.get_figure_settings().set_limits(
            self._history_states[self._history_pos][1],
        )
        self.props.can_redo = True
        self.props.can_undo = \
            abs(self._history_pos) < len(self._history_states)
        self._set_data_copy()
        self.add_view_history_state()

    def redo(self) -> None:
        if not self.props.can_redo:
            return
        self._history_pos += 1
        state = self._history_states[self._history_pos]
        items_changed = False
        for change_type, change in state[0]:
            if change_type == 0:
                self[change[0]].set_property(change[1], change[3])
            elif change_type == 1:
                self._add_item(item.new_from_dict(copy.deepcopy(change)))
                items_changed = True
            elif change_type == 2:
                self._delete_item(change[1]["uuid"])
                items_changed = True
            elif change_type == 3:
                self.change_position(change[1], change[0])
                items_changed = True
            elif change_type == 4:
                self.props.figure_settings.set_property(
                    change[0], change[2],
                )
        if items_changed:
            self.notify("items")
            self.notify("empty")
        self.notify("items_selected")
        self.get_figure_settings().set_limits(state[1])
        self.props.can_redo = self._history_pos < -1
        self.props.can_undo = True
        self._set_data_copy()
        self.add_view_history_state()

    def add_view_history_state(self) -> None:
        limits = self.get_figure_settings().get_limits()
        if all(
            math.isclose(old, new) for old, new
            in zip(self._view_history_states[-1], limits)
        ):
            return
        # If a couple of redo's were performed previously, it deletes the
        # clipboard data that is located after the current clipboard
        # position and disables the redo button
        if self._view_history_pos != -1:
            self._view_history_states = \
                self._view_history_states[:self._view_history_pos + 1]
        self._view_history_pos = -1
        self._view_history_states.append(limits)
        self.props.can_view_back = True
        self.props.can_view_forward = False
        self.change_unsaved(True)

    def view_back(self) -> None:
        if not self.props.can_view_back:
            return
        self._view_history_pos -= 1
        self.get_figure_settings().set_limits(
            self._view_history_states[self._view_history_pos],
        )
        self.props.can_view_forward = True
        self.props.can_view_back = \
            abs(self._view_history_pos) < len(self._view_history_states)

    def view_forward(self) -> None:
        if not self.props.can_view_forward:
            return
        self._view_history_pos += 1
        self.get_figure_settings().set_limits(
            self._view_history_states[self._view_history_pos],
        )
        self.props.can_view_back = True
        self.props.can_view_forward = self._view_history_pos < -1

    def optimize_limits(self) -> None:
        figure_settings = self.get_figure_settings()
        axes = [
            [direction, False, [], [],
             figure_settings.get_property(f"{direction}_scale")]
            for direction in ("bottom", "left", "top", "right")
        ]
        for item_ in self:
            if not isinstance(item_, item.DataItem):
                continue
            for index in \
                    item_.get_xposition() * 2, 1 + item_.get_yposition() * 2:
                axes[index][1] = True
                xydata = numpy.asarray(
                    item_.ydata if index % 2 else item_.xdata,
                )
                try:
                    xydata = xydata[numpy.isfinite(xydata)]
                except TypeError:
                    return
                nonzero_data = \
                    numpy.array([value for value in xydata if value != 0])
                axes[index][2].append(
                    nonzero_data.min()
                    if axes[index][4] in (1, 4) and len(nonzero_data) > 0
                    else xydata.min(),
                )
                axes[index][3].append(xydata.max())

        for count, (direction, used, min_all, max_all, scale) in \
                enumerate(axes):
            if not used:
                continue
            min_all = min(min_all)
            max_all = max(max_all)
            if scale != 1:  # For non-logarithmic scales
                span = max_all - min_all
                # 0.05 padding on y-axis, 0.015 padding on x-axis
                padding_factor = 0.05 if count % 2 else 0.015
                max_all += padding_factor * span

                # For inverse scale, calculate padding using a factor
                min_all = (min_all - padding_factor * span if scale != 4
                           else min_all * 0.99)
            else:  # Use different scaling type for logarithmic scale
                # Use padding factor of 2 for y-axis, 1.025 for x-axis
                padding_factor = 2 if count % 2 else 1.025
                min_all *= 1 / padding_factor
                max_all *= padding_factor
            figure_settings.set_property(f"min_{direction}", min_all)
            figure_settings.set_property(f"max_{direction}", max_all)
        self.add_view_history_state()

    def to_project_dict(self) -> dict[str, Any]:
        figure_settings = self.get_figure_settings()
        return {
            "version": self.get_application().get_version(),
            "data": [item_.to_dict() for item_ in self],
            "figure-settings": {
                key: figure_settings.get_property(key)
                for key in dir(figure_settings.props)
            },
            "history-states": self._history_states,
            "history-position": self._history_pos,
            "view-history-states": self._view_history_states,
            "view-history-position": self._view_history_pos,
            "project-uri": self.props.project_uri
        }

    def change_unsaved(self, unsaved):
        """Proof of concept placeholder"""
        self.props.unsaved = unsaved
        title = \
            self.get_application().get_window().get_content_title().get_title()
        if title.startswith("• "):
            title = title.split("• ")[-1]

        if unsaved:
            prefix = "• "
            self.get_application().get_window().get_content_title().set_title(
                prefix + title)
            if self.props.project_uri == "":
                self.get_application().get_window().get_content_title().set_subtitle("Draft")
            else:
                uri_parse  = urlparse(self.props.project_uri)
                filepath = os.path.abspath(os.path.join(uri_parse.netloc, uri_parse.path))
                filepath = filepath.replace(os.path.expanduser("~"), "~")
                self.get_application().get_window().get_content_title().set_subtitle(filepath)
        else:
            self.get_application().get_window().get_content_title().set_title(
                title)

    def load_from_project_dict(self,
                               project_dict: dict[str, Any],
                               project_uri: str) -> None:
        figure_settings = self.get_figure_settings()
        for key, value in project_dict["figure-settings"].items():
            if figure_settings.get_property(key) != value:
                figure_settings.set_property(key, value)
        self.set_items(item.new_from_dict(d) for d in project_dict["data"])
        self._set_data_copy()
        self.project_uri = project_uri
        self._history_states = project_dict["history-states"]
        self._history_pos = project_dict["history-position"]
        self._view_history_states = project_dict["view-history-states"]
        self._view_history_pos = project_dict["view-history-position"]

        self.props.can_undo = \
            abs(self._history_pos) < len(self._history_states)
        self.props.can_redo = self._history_pos < -1
        self.props.can_view_back = \
            abs(self._view_history_pos) < len(self._view_history_states)
        self.props.can_view_forward = self._view_history_pos < -1
        filename = Path(project_uri).stem
        uri_parse  = urlparse(project_uri)
        filepath = os.path.abspath(os.path.join(uri_parse.netloc, uri_parse.path))
        filepath = filepath.replace(os.path.expanduser("~"), "~")
        self.get_application().get_window().get_content_title().set_title(
            filename)
        self.get_application().get_window().get_content_title().set_subtitle(
            filepath)
