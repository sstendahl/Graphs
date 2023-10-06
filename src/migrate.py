# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import pickle
import sys
from pathlib import Path

from gi.repository import GLib, Gio

from graphs import file_io, misc, utilities


CONFIG_MIGRATION_TABLE = {
    # old-key: (category, key)
    "action_center_data": ("general", "center"),
    "addequation_equation": ("add-equation", "equation"),
    "addequation_step_size": ("add-equation", "step-size"),
    "addequation_x_start": ("add-equation", "x-start"),
    "addequation_x_stop": ("add-equation", "x-stop"),
    "export_figure_dpi": ("export-figure", "dpi"),
    "export_figure_transparent": ("export-figure", "transparent"),
    "handle_duplicates": ("general", "handle-duplicates"),
    "hide_unselected": ("general", "hide-unselected"),
    "override_style_change": ("general", "override-item-properties"),
    "plot_custom_style": ("figure", "custom-style"),
    "plot_legend": ("figure", "legend"),
    "plot_right_label": ("figure", "right-label"),
    "plot_right_scale": ("figure", "right-scale"),
    "plot_title": ("figure", "title"),
    "plot_top_label": ("figure", "top-label"),
    "plot_top_scale": ("figure", "top-scale"),
    "plot_use_custom_style": ("figure", "use-custom-style"),
    "plot_x_label": ("figure", "bottom-label"),
    "plot_x_position": ("general", "x-position"),
    "plot_x_scale": ("figure", "bottom-scale"),
    "plot_y_label": ("figure", "left-label"),
    "plot_y_position": ("general", "y-position"),
    "plot_y_scale": ("figure", "left-scale"),
}


def migrate_config(settings):
    """Migrate old file-based user config to dconf"""
    main_dir = Gio.File.new_for_path(GLib.get_user_config_dir())
    old_config_dir = main_dir.get_child_for_display_name("Graphs")
    if not old_config_dir.query_exists(None):
        return
    new_config_dir = utilities.get_config_directory()
    config_file = old_config_dir.get_child_for_display_name("config.json")
    import_file = old_config_dir.get_child_for_display_name("import.json")
    old_styles_dir = old_config_dir.get_child_for_display_name("styles")
    if config_file.query_exists(None):
        _migrate_config(settings, config_file)
    if import_file.query_exists(None):
        _migrate_import_params(settings, import_file)
    if old_styles_dir.query_exists(None):
        _migrate_styles(old_styles_dir, new_config_dir)
    old_config_dir.delete(None)


def _migrate_config(settings_, config_file):
    config = file_io.parse_json(config_file)
    for old_key, (category, key) in CONFIG_MIGRATION_TABLE.items():
        with contextlib.suppress(KeyError):
            settings = settings_.get_child(category)
            value = config[old_key]
            if "scale" in key:
                value = value.capitalize()
            if isinstance(value, str):
                settings.set_string(key, value)
            elif isinstance(value, bool):
                settings.set_boolean(key, value)
            elif isinstance(value, int):
                settings.set_int(key, value)
    config_file.delete(None)


def _migrate_import_params(settings_, import_file):
    for mode, params in file_io.parse_json(import_file).items():
        settings = settings_.get_child("import-params").get_child(mode)
        for key, value in params.items():
            if key == "separator":
                settings.set_string(key, f"{value} ")
            elif isinstance(value, str):
                settings.set_string(key, value)
            elif isinstance(value, int):
                settings.set_int(key.replace("_", "-"), value)
    import_file.delete(None)


SYSTEM_STYLES = [
    "adwaita", "adwaita-dark", "bmh", "classic", "dark-background",
    "fivethirtyeight", "ggplot", "grayscale", "seaborn", "seaborn-bright",
    "seaborn-colorblind", "seaborn-dark", "seaborn-darkgrid",
    "seaborn-dark-pallete", "seaborn-deep", "seaborn-muted",
    "seaborn-notebook", "seaborn-paper", "seaborn-pastel", "seaborn-poster",
    "seaborn-talk", "seaborn-ticks", "seaborn-white", "seaborn-whitegrid",
    "solarized-light", "tableu-colorblind10", "thesis", "yaru", "yaru-dark",
]


def _migrate_styles(old_styles_dir, new_config_dir):
    new_styles_dir = new_config_dir.get_child_for_display_name("styles")
    if not new_styles_dir.query_exists(None):
        new_styles_dir.make_directory_with_parents()
    enumerator = old_styles_dir.enumerate_children("default::*", 0, None)
    while True:
        file_info = enumerator.next_file(None)
        if file_info is None:
            break
        file = enumerator.get_child(file_info)
        stylename = Path(utilities.get_filename(file)).stem
        if stylename not in SYSTEM_STYLES:
            params = file_io.parse_style(file)
            adwaita = Gio.File.new_for_uri(
                "resource:///se/sjoerd/Graphs/styles/adwaita.mplstyle",
            )
            for key, value in file_io.parse_style(adwaita).items():
                if key not in params:
                    params[key] = value
            params.name = stylename
            file_io.write_style(new_styles_dir.get_child_for_display_name(
                f"{stylename.lower().replace(' ', '-')}.mplstyle",
            ), params)
        file.delete(None)
    enumerator.close(None)
    old_styles_dir.delete(None)


ITEM_MIGRATION_TABLE = {
    "plot_x_position": "xposition",
    "plot_y_position": "yposition",
    "x_anchor": "xanchor",
    "y_anchor": "yanchor",
    "key": "uuid",
}

ITEM_VALUE_MIGRATION_TABLE = {
    "linestyle": ["none", "solid", "dotted", "dashed", "dashdot"],
    "markerstyle": ["none", ".", ",", "o", "v", "^", "<", ">", "8", "s", "p",
                    "*", "h", "H", "+", "x", "D", "d", "|", "_", "P", "X"],
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
}

LEGEND_POSITIONS = [
    "best", "upper right", "upper left", "lower left", "lower right",
    "center left", "center right", "lower center", "upper center", "center",
]


class PlotSettings:
    def migrate(self) -> dict:
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
    def migrate(self) -> dict:
        dictionary = {"item_type": self.item_type}
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
    item_type = "GraphsDataItem"


class TextItem(ItemBase):
    item_type = "GraphsTextItem"


DEFAULT_VIEW = [0, 1, 0, 10, 0, 1, 0, 10]


def migrate_project(file):
    sys.modules["graphs.misc"] = sys.modules[__name__]
    sys.modules["graphs.item"] = sys.modules[__name__]
    project = pickle.loads(file_io.read_file(file, None))

    figure_settings = project["plot_settings"].migrate()
    current_limits = [figure_settings[key] for key in misc.LIMITS]
    history_pos = project["clipboard_pos"]
    history_states = _migrate_clipboard(
        project["datadict_clipboard"], history_pos, current_limits,
    )

    return {
        "version": project["version"],
        "data": [item.migrate() for item in project["data"].values()],
        "figure-settings": figure_settings,
        "history-states": history_states,
        "history-position": history_pos,
        "view-history-states": [DEFAULT_VIEW.copy(), current_limits],
        "view-history-position": -1,
    }


def _migrate_clipboard(clipboard, clipboard_pos, current_limits):
    if not clipboard:
        return []
    new_clipboard = []
    if len(clipboard) > 100:
        clipboard = clipboard[len(clipboard) - 100:]
    states = [
        {item.uuid: item.migrate() for item in state.values()}
        for state in clipboard
    ]
    new_clipboard.append(([], DEFAULT_VIEW.copy()))
    initial_items = states[1].values()
    new_clipboard.append(
        ([(1, item) for item in initial_items], _get_limits(initial_items)),
    )
    if len(states) > 2:
        for count in range(len(states) - 2):
            batch = []
            previous_state = states[count + 1]
            current_state = states[count + 2]
            if len(current_state) < len(previous_state):
                for key, item in previous_state.copy().items():
                    if key not in current_state:
                        batch.append((2, previous_state.index(item), item))
                        previous_state.pop(item)
            for count_2, (key, item) in enumerate(current_state.items()):
                if key in previous_state:
                    previous_index = list(previous_state.keys()).index(key)
                    if previous_index != count_2:
                        batch.append((3, (previous_index, count_2)))
                    else:
                        for key_2, value in item.items():
                            previous_value = previous_state[key][key_2]
                            if value != previous_value:
                                batch.append(
                                    (0, (key, key_2, previous_value, value)),
                                )
                else:
                    batch.append((1, item))
            if clipboard_pos == count - len(states) + 1:
                limits = _get_limits(current_state.values())
            else:
                limits = current_limits
            new_clipboard.append((batch, limits))
    return new_clipboard


def _get_limits(items):
    limits = [None] * 8
    for item in items:
        if item["item_type"] != "Item":
            continue
        for count, x_or_y in enumerate(["x", "y"]):
            try:
                limits[item[f"{x_or_y}position"] * 2 + 4 * count] = min(
                    limits[item[f"{x_or_y}position"] * 2 + 4 * count],
                    min(item[f"{x_or_y}data"]),
                )
            except TypeError:
                limits[item[f"{x_or_y}position"] * 2 + 4 * count] = \
                    min(item[f"{x_or_y}data"])
            try:
                limits[item[f"{x_or_y}position"] * 2 + 4 * count + 1] = max(
                    limits[item[f"{x_or_y}position"] * 2 + 4 * count + 1],
                    max(item[f"{x_or_y}data"]),
                )
            except TypeError:
                limits[item[f"{x_or_y}position"] * 2 + 4 * count + 1] = \
                    max(item[f"{x_or_y}data"])
    for count in range(8):
        if limits[count] is None:
            limits[count] = DEFAULT_VIEW.copy()[count]
    return limits
