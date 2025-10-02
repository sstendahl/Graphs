# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for saving and loading projects."""
import copy
import logging
import re
from gettext import gettext as _
from operator import itemgetter

from gi.repository import Gio, Graphs

from graphs import file_io, item, migrate
from graphs.misc import ChangeType

CURRENT_PROJECT_VERSION = 2


class ProjectParseError(Exception):
    """Custom error for parsing projects."""

    def __init__(self, message: str, log: bool = True):
        super().__init__()
        self.message = message
        self.log = log


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

    beta_pattern = re.compile(r"^\d+\.\d+\.\d+-[0-9a-f]{8}$")

    def __init__(
        self,
        project_dict: dict,
        parse_flags: Graphs.ProjectParseFlags,
    ):
        # Verify all keys are present
        try:
            for key in PROJECT_KEYS:
                project_dict[key]
        except KeyError as e:
            raise ProjectParseError(_("Project file is missing data")) from e

        self._project_dict = project_dict
        self.parse_flags = parse_flags

        # check beta version
        beta_version = bool(self.beta_pattern.match(project_dict["version"]))
        check_beta = not parse_flags & Graphs.ProjectParseFlags.ALLOW_BETA
        if beta_version and check_beta:
            raise ProjectParseError("BETA_DISALLOWED", False)

    def migrate(self) -> dict:
        """Perform needed migrations."""
        try:
            project_version = int(self._project_dict["project-version"])
            assert project_version > 0
        except KeyError:
            project_version = 1

        if project_version > CURRENT_PROJECT_VERSION:
            raise ProjectParseError(
                _("Project is from a newer incompatible version of Graphs"),
            )

        if CURRENT_PROJECT_VERSION == project_version:
            return self._project_dict

        # Migrate a project one version at a time
        current_version = project_version
        while current_version < CURRENT_PROJECT_VERSION:
            current_version += 1
            getattr(self, f"_migrate_v{current_version}")()
        return self._project_dict

    def _migrate_v2(self):
        logging.debug("migrating project v1 to v2")
        # Figure settings entries are now properly stored in hyphon-case
        self._project_dict["figure-settings"] = {
            key.replace("_", "-"): value
            for (key, value) in self._project_dict["figure-settings"].items()
        }

        self._migrate_inserted_scale(2)  # log2 scale added

        # Handle items no longer making use of uuid
        def _item_dict_without_uuid(item_):
            return {
                key: value
                for (key, value) in item_.items() if key != "uuid"
            }

        item_positions = []
        data = []
        for item_ in self._project_dict["data"]:
            item_positions.append(item_["uuid"])
            data.append(_item_dict_without_uuid(item_))
        self._project_dict["data"] = data
        history_states = self._project_dict["history-states"]
        n_states = len(history_states)
        history_pos = self._project_dict["history-position"]
        while history_pos < 1:
            for (change_type, change) in history_states[history_pos][0]:
                match ChangeType(change_type):
                    case ChangeType.ITEM_ADDED:
                        item_positions.append(change["uuid"])
                    case ChangeType.ITEM_REMOVED:
                        item_positions.remove(change[1]["uuid"])
                    case ChangeType.ITEMS_SWAPPED:
                        uuid = item_positions.pop(change[0])
                        item_positions.insert(change[1], uuid)
            history_pos += 1
        for state_index, state in enumerate(reversed(history_states)):
            state_index = n_states - state_index - 1
            n_changes = len(state[0])
            for change_index, (change_type, change) \
                    in enumerate(reversed(state[0])):
                change_index = n_changes - change_index - 1
                match ChangeType(change_type):
                    case ChangeType.ITEM_ADDED:
                        item_positions.remove(change["uuid"])
                        history_states[state_index][0][change_index][1] = \
                            _item_dict_without_uuid(change)
                    case ChangeType.ITEM_REMOVED:
                        item_positions.insert(change[0], change[1]["uuid"])
                        history_states[state_index][0][change_index][1] = \
                            [change[0], _item_dict_without_uuid(change[1])]
                    case ChangeType.ITEMS_SWAPPED:
                        uuid = item_positions.pop(change[1])
                        item_positions.insert(change[0], uuid)
                    case ChangeType.ITEM_PROPERTY_CHANGED:
                        change[0] = item_positions.index(change[0])
                        history_states[state_index][0][change_index][1] = \
                            change
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


class ProjectValidator:
    """Validate the project."""

    def __init__(
        self,
        project_dict: dict,
        parse_flags: Graphs.ProjectParseFlags,
    ):
        self.project_dict = copy.deepcopy(project_dict)
        self.parse_flags = parse_flags

    def validate(self):
        """Run through the history states."""
        # Validate Figure Settings
        self.figure_settings = Graphs.FigureSettings(
            **{
                key.replace("-", "_"): val
                for (key, val) in self.project_dict["figure-settings"].items()
            },
        )

        # Validate items
        self.items = [item.new_from_dict(d) for d in self.project_dict["data"]]

        # Validate view history
        view_history_states = self.project_dict["view-history-states"]
        for history_state in view_history_states:
            self.figure_settings.set_limits(history_state)
        view_history_pos = int(self.project_dict["view-history-position"])
        assert view_history_pos < 0
        assert abs(view_history_pos) <= len(view_history_states)

        # Validate data history
        history_states = self.project_dict["history-states"]
        history_pos = int(self.project_dict["history-position"])
        assert history_pos < 0
        assert abs(history_pos) <= len(history_states)
        while history_pos < -1:
            for (change_type, change) in history_states[history_pos][0]:
                match ChangeType(change_type):
                    case ChangeType.ITEM_PROPERTY_CHANGED:
                        index, prop, value = itemgetter(0, 1, 3)(change)
                        self.items[index].set_property(prop, value)
                    case ChangeType.ITEM_ADDED:
                        item_dict_copy = copy.deepcopy(change)
                        self.items.append(item.new_from_dict(item_dict_copy))
                    case ChangeType.ITEM_REMOVED:
                        self.items.pop(change[0])
                    case ChangeType.ITEMS_SWAPPED:
                        item_ = self.items.pop(change[0])
                        self.items.insert(change[1], item_)
                    case ChangeType.FIGURE_SETTINGS_CHANGED:
                        self.figure_settings.set_property(change[0], change[2])
            history_pos += 1
        for history_state in reversed(history_states):
            self.figure_settings.set_limits(history_state[1])
            for change_type, change in reversed(history_state[0]):
                match ChangeType(change_type):
                    case ChangeType.ITEM_PROPERTY_CHANGED:
                        index, prop, value = itemgetter(0, 1, 2)(change)
                        self.items[index].set_property(prop, value)
                    case ChangeType.ITEM_ADDED:
                        self.items.pop()
                    case ChangeType.ITEM_REMOVED:
                        item_ = item.new_from_dict(copy.deepcopy(change[1]))
                        self.items.insert(change[0], item_)
                    case ChangeType.ITEMS_SWAPPED:
                        item_ = self.items.pop(change[1])
                        self.items.insert(change[0], item_)
                    case ChangeType.FIGURE_SETTINGS_CHANGED:
                        self.figure_settings.set_property(change[0], change[1])


def read_project_file(
    file: Gio.File,
    parse_flags: Graphs.ProjectParseFlags = Graphs.ProjectParseFlags.NONE,
) -> dict:
    """Read a project dict from file and account for migration."""
    try:
        project_dict = file_io.parse_json(file)
    except UnicodeDecodeError:
        if not parse_flags & Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION:
            raise ProjectParseError("LEGACY_MIGRATION_DISALLOWED", False)
        try:
            project_dict = migrate.migrate_project(file)
        except Exception as e:
            raise ProjectParseError(_("Failed to do legacy migration")) from e
    except Exception as e:
        raise ProjectParseError(_("Failed to parse project file")) from e
    try:
        project_dict = ProjectMigrator(project_dict, parse_flags).migrate()
    except ProjectParseError:
        raise
    except Exception as e:
        raise ProjectParseError(_("Failed to migrate project")) from e
    try:
        ProjectValidator(project_dict, parse_flags).validate()
    except ProjectParseError:
        raise
    except Exception as e:
        raise ProjectParseError(_("Failed to validate project")) from e
    return project_dict


def save_project_dict(file: Gio.File, project_dict: dict) -> None:
    """Save a project dict to a file."""
    project_dict["project-version"] = CURRENT_PROJECT_VERSION
    file_io.write_json(file, project_dict, pretty_print=False)
