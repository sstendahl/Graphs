# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for saving and loading projects."""
import logging
from gettext import gettext as _

from gi.repository import Gio

from graphs import file_io, migrate

CURRENT_PROJECT_VERSION = 2


class ProjectParseError(Exception):
    """Custom error for parsing projects."""

    def __init__(self, message: str):
        super().__init__()
        self.message = message


PROJECT_KEYS = [
    "version",
    "data",
    "figure-settings",
    "history-states",
    "history-position",
    "view-history-states",
    "view-history-position",
]


class ProjectMigrator:
    """
    Migrate project data to be compatible with the current version of Graphs.

    Migration is based on version to version basis, so migrating from v1 to v3
    would involve migrating from v1 to v2 first and then migrating from v2
    to v3.
    """

    def __init__(self, project_dict: dict):
        # Verify all keys are present
        try:
            for key in PROJECT_KEYS:
                project_dict[key]
        except KeyError as e:
            raise ProjectParseError(_("Project file is missing data")) from e

        self._project_dict = project_dict

    def migrate(self) -> dict:
        """Perform needed migrations."""
        try:
            project_version = self._project_dict["project-version"]
        except KeyError:
            project_version = 1

        if project_version > CURRENT_PROJECT_VERSION:
            raise ProjectParseError(
                _("Project is from a newer incompatible version of Graphs"),
            )

        if CURRENT_PROJECT_VERSION == project_version:
            return self._project_dict

        # Migrate a project one version at a time
        for version in range(CURRENT_PROJECT_VERSION - project_version):
            getattr(self, f"_migrate_v{version + 2}")()
        return self._project_dict

    def _migrate_v2(self):
        logging.debug("migrating project v1 to v2")
        # Figure settings entries are now properly stored in hyphon-case
        self._project_dict["figure-settings"] = {
            key.replace("_", "-"): value
            for key, value in self._project_dict["figure-settings"].items()
        }

        # Migrate v1 to v2
        self._migrate_inserted_scale(2)  # log2 scale added

        # Handle items no longer making use of uuid
        def _item_dict_without_uuid(item):
            return {key: value for key, value in item.items() if key != "uuid"}

        item_positions = []
        data = []
        for item in self._project_dict["data"]:
            item_positions.append(item["uuid"])
            data.append(_item_dict_without_uuid(item))
        self._project_dict["data"] = data
        history_states = self._project_dict["history-states"]
        n_states = len(history_states)
        for state_index, state in enumerate(reversed(history_states)):
            state_index = n_states - state_index - 1
            n_changes = len(state[0])
            for change_index, changeset in enumerate(reversed(state[0])):
                change_index = n_changes - change_index - 1
                change_type, change = changeset
                if change_type == 1:
                    item_positions.remove(change["uuid"])
                    history_states[state_index][0][change_index][1] = \
                        _item_dict_without_uuid(change)
                elif change_type == 2:
                    r_index = change[0]
                    item_positions = item_positions[:r_index] \
                        + [change[1]["uuid"]] \
                        + item_positions[r_index:]
                    history_states[state_index][0][change_index][1] = \
                        (change[0], _item_dict_without_uuid(change[1]))
                elif change_type == 0:
                    change[0] = item_positions.index(change[0])
                    history_states[state_index][0][change_index][1] = change
        self._project_dict["history-states"] = history_states

    def _migrate_inserted_scale(self, scale_index: int) -> None:
        """Handle a new scale being inserted at scale_index."""
        figure_settings = self._project_dict["figure-settings"]
        for prefix in ("left", "right", "top", "bottom"):
            axis = prefix + "-scale"
            if figure_settings[axis] >= scale_index:
                figure_settings[axis] = figure_settings[axis] + 1

        for state_index, history_state in enumerate(
            self._project_dict["history-states"],
        ):
            for change_index, changeset in enumerate(history_state[0]):
                change_type, change = changeset
                if change_type != 4:
                    continue
                if change[0][-6:] != "-scale":
                    continue
                for i, val in enumerate(change[1:], 1):
                    if val >= scale_index:
                        self._project_dict["history-states"][state_index][0][
                            change_index][1][i] = val + 1


def read_project_file(file: Gio.File) -> dict:
    """Read a project dict from file and account for migration."""
    try:
        project_dict = file_io.parse_json(file)
    except UnicodeDecodeError:
        project_dict = migrate.migrate_project(file)
    return ProjectMigrator(project_dict).migrate()


def save_project_dict(file: Gio.File, project_dict: dict) -> None:
    """Save a project dict to a file."""
    project_dict["project-version"] = CURRENT_PROJECT_VERSION
    file_io.write_json(file, project_dict, pretty_print=False)
