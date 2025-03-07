# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for migrating old data to new structures."""
import contextlib
import logging
import pickle
import sys

from gi.repository import Gio

import gio_pyio

from graphs import misc


ITEM_MIGRATION_TABLE = {
    "plot_x_position": "xposition",
    "plot_y_position": "yposition",
    "x_anchor": "xanchor",
    "y_anchor": "yanchor",
    "key": "uuid",
}

ITEM_VALUE_MIGRATION_TABLE = {
    "linestyle": ["none", "solid", "dotted", "dashed", "dashdot"],
    "markerstyle": [
        "none",
        ".",
        ",",
        "o",
        "v",
        "^",
        "<",
        ">",
        "8",
        "s",
        "p",
        "*",
        "h",
        "H",
        "+",
        "x",
        "D",
        "d",
        "|",
        "_",
        "P",
        "X",
    ],
    "xposition": ["bottom", "top"],
    "yposition": ["left", "right"],
}

PLOT_SETTINGS_MIGRATION_TABLE = {
    "xlabel": "bottom_label",
    "ylabel": "left_label",
    "xscale": "bottom_scale",
    "yscale": "left_scale",
    "use_custom_plot_style": "use_custom_style",
    "custom_plot_style": "custom_style",
    "mix_right": "min_right",
}

LEGEND_POSITIONS = [
    "best",
    "upper right",
    "upper left",
    "lower left",
    "lower right",
    "center left",
    "center right",
    "lower center",
    "upper center",
    "center",
]


class PlotSettings:
    """Old PlotSettings standin."""

    def migrate(self) -> dict:
        """Migrate class to dict."""
        dictionary = {}
        for key, value in self.__dict__.items():
            with contextlib.suppress(KeyError):
                key = PLOT_SETTINGS_MIGRATION_TABLE[key]
            if "scale" in key:
                value = 0 if value == "linear" else 1
            elif key == "legend_position":
                value = LEGEND_POSITIONS.index(value)
            dictionary[key] = value
        return dictionary


class ItemBase:
    """Old ItemBase standin."""

    def migrate(self) -> dict:
        """Migrate class to dict."""
        dictionary = {"type": self.item_type}
        for key, value in self.__dict__.items():
            with contextlib.suppress(KeyError):
                key = ITEM_MIGRATION_TABLE[key]
            if key in ITEM_VALUE_MIGRATION_TABLE:
                try:
                    value = ITEM_VALUE_MIGRATION_TABLE[key].index(value)
                except IndexError:
                    value = 0
            dictionary[key] = value
        return dictionary


class Item(ItemBase):
    """Old Item standin."""

    item_type = "GraphsDataItem"


class TextItem(ItemBase):
    """Old TextItem standin."""

    item_type = "GraphsTextItem"


_DEFAULT_VIEW = [0, 1, 0, 10, 0, 1, 0, 10]


def migrate_project(file: Gio.File) -> dict:
    """Migrate pickle-based project."""
    logging.debug("Migrating legacy project")
    sys.modules["graphs.misc"] = sys.modules[__name__]
    sys.modules["graphs.item"] = sys.modules[__name__]
    with gio_pyio.open(file, "rb") as wrapper:
        project = pickle.load(wrapper)

    figure_settings = project["plot_settings"].migrate()
    current_limits = [figure_settings[key] for key in misc.LIMITS]
    history_pos = int(project["clipboard_pos"])
    history_states = _migrate_clipboard(
        project["datadict_clipboard"],
        history_pos,
        current_limits,
    )

    return {
        "version": str(project["version"]),
        "project-version": 1,
        "data": [item.migrate() for item in project["data"].values()],
        "figure-settings": figure_settings,
        "history-states": history_states,
        "history-position": history_pos,
        "view-history-states": [_DEFAULT_VIEW.copy(), current_limits],
        "view-history-position": -1,
    }


def _migrate_clipboard(clipboard, clipboard_pos, current_limits):
    if not clipboard:
        return []
    new_clipboard = []
    if len(clipboard) > 100:
        clipboard = list(clipboard[len(clipboard) - 100:])
    states = [{
        item.key: item.migrate()
        for item in state.values()
    } for state in clipboard]
    new_clipboard.append([[], _DEFAULT_VIEW.copy()])
    initial_items = states[1].values()
    new_clipboard.append((
        [[1, item] for item in initial_items],
        _get_limits(initial_items),
    ))
    if len(states) > 2:
        for count in range(len(states) - 2):
            batch = []
            previous_state = states[count + 1]
            current_state = states[count + 2]
            if len(current_state) < len(previous_state):
                for key, item in previous_state.copy().items():
                    if key not in current_state:
                        batch.append([2, [previous_state.index(item), item]])
                        previous_state.pop(item)
            for count_2, (key, item) in enumerate(current_state.items()):
                if key in previous_state:
                    previous_index = list(previous_state.keys()).index(key)
                    if previous_index != count_2:
                        batch.append([3, [previous_index, count_2]])
                    else:
                        for key_2, value in item.items():
                            previous_value = previous_state[key][key_2]
                            if value != previous_value:
                                batch.append(
                                    [0, [key, key_2, previous_value, value]],
                                )
                else:
                    batch.append([1, item])
            if clipboard_pos == count - len(states) + 1:
                limits = _get_limits(current_state.values())
            else:
                limits = current_limits
            new_clipboard.append([batch, limits])
    return new_clipboard


def _get_limits(items):
    limits = [None] * 8
    for item in items:
        if item["type"] != "Item":
            continue
        for count, x_or_y in enumerate(["x", "y"]):
            index = item[f"{x_or_y}position"] * 2 + 4 * count
            data = item[f"{x_or_y}data"]
            try:
                limits[index] = min(limits[index], data)
            except TypeError:
                limits[index] = min(data)
            try:
                limits[index + 1] = max(limits[index + 1], data)
            except TypeError:
                limits[index + 1] = max(data)
    for count in range(8):
        default_view_copy = _DEFAULT_VIEW.copy()
        if limits[count] is None:
            limits[count] = default_view_copy[count]
    return limits
