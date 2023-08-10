# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import pickle
import sys

from graphs import file_io, utilities


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
    "plot_x_position": ("figure", "x-position"),
    "plot_x_scale": ("figure", "bottom-scale"),
    "plot_y_label": ("figure", "left-label"),
    "plot_y_position": ("figure", "y-position"),
    "plot_y_scale": ("figure", "left-scale"),
}


def migrate_config(self):
    """Migrate old file-based user config to dconf"""
    config_dir = utilities.get_config_directory()
    if not config_dir.query_exists(None):
        return
    config_file = config_dir.get_child_for_display_name("config.json")
    import_file = config_dir.get_child_for_display_name("import.json")
    if config_file.query_exists(None):
        _migrate_config(self, config_file)
    if config_file.query_exists(None):
        _migrate_import_params(self, import_file)


def _migrate_config(self, config_file):
    config = file_io.parse_json(config_file)
    for old_key, (category, key) in CONFIG_MIGRATION_TABLE.items():
        with contextlib.suppress(KeyError):
            settings = self.settings.get_child(category)
            value = config[old_key]
            if isinstance(value, str):
                settings.set_string(key, value)
            elif isinstance(value, bool):
                settings.set_boolean(key, value)
            elif isinstance(value, int):
                settings.set_int(key, value)
    config_file.delete(None)


def _migrate_import_params(self, import_file):
    for mode, params in file_io.parse_json(import_file).items():
        settings = self.settings.get_child("import-params").get_child(mode)
        for key, value in params.items():
            if key == "separator":
                settings.set_string(key, f"{value} ")
            elif isinstance(value, str):
                settings.set_string(key, value)
            elif isinstance(value, int):
                settings.set_int(key, value)
    import_file.delete(None)


class PlotSettings:
    pass

class Item:
    pass


DEFAULT_VIEW = {
    "min_bottom": 0,
    "max_bottom": 1,
    "min_top": 0,
    "max_top": 10,
    "min_left": 0,
    "max_left": 1,
    "min_right": 0,
    "max_right": 10,
}


def migrate_project(file):
    sys.modules["graphs.misc"] = sys.modules[__name__]
    sys.modules["graphs.item"] = sys.modules[__name__]
    project = pickle.loads(file_io.read_file(file, None))

    return {
        "version": project["version"],
        "data": [_migrate_item(item) for item in project["data"].values()],
        "figure-settings": _migrate_plot_settings(project["plot_settings"]),
        "data-clipboard": [{"data": [],
                            "view": DEFAULT_VIEW.copy()}],
        "data-clipboard-position": project["clipboard_pos"],
        "view-clipboard": None,
        "view-clipboard-position": None,
    }


ITEM_MIGRATION_TABLE = {
    "plot_x_position": "xposition",
    "plot_y_position": "yposition",
}


def _migrate_item(item: Item) -> dict:
    dictionary = {
        ITEM_MIGRATION_TABLE[key] if key in ITEM_MIGRATION_TABLE
        else key: value for key, value in item.__dict__.items()
    }
    dictionary["item_type"] = "Item"
    return dictionary

PLOT_SETTINGS_MIGRATION_TABLE = {
    "xlabel": "bottom_label",
    "ylabel": "left_label",
    "xscale": "bottom_scale",
    "yscale": "left_scale",
    "use_custom_plot_style": "use_custom_style",
    "custom_plot_style": "custom_style",
}

def _migrate_plot_settings(item: Item) -> dict:
    return {
        PLOT_SETTINGS_MIGRATION_TABLE[key]
        if key in PLOT_SETTINGS_MIGRATION_TABLE
        else key: value for key, value in item.__dict__.items()
    }
