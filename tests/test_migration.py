# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for project migration."""
import copy
import json
import os

from gi.repository import Gio, Graphs

from graphs.project import ProjectMigrator, ProjectValidator, read_project_file

import pytest

PROJECTFILE_V1 = os.path.join(os.path.dirname(__file__), "project_v1.graphs")


@pytest.fixture
def v1_project_dict():
    """Load the legacy v1 project dict from the test fixture."""
    with open(PROJECTFILE_V1) as f:
        return json.load(f)


@pytest.fixture
def migrated_project_dict(v1_project_dict):
    """Return the migrated dict from the legacy fixture."""
    return ProjectMigrator(
        copy.deepcopy(v1_project_dict),
        Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    ).migrate()


@pytest.fixture
def validated_project(migrated_project_dict):
    """Return a ProjectValidator after validating the migrated dict."""
    validator = ProjectValidator(
        migrated_project_dict,
        Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    )
    validator.validate()
    return validator


def test_read_old_project_file():
    """Test if read_project_file parses the v1 file without errors."""
    file = Gio.File.new_for_path(PROJECTFILE_V1)
    result = read_project_file(
        file, Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    )
    assert "data" in result
    assert "figure-settings" in result


def test_migration_completes_without_error(migrated_project_dict):
    """Test if migrate returns a dict with the expected top-level keys."""
    assert "data" in migrated_project_dict
    assert "figure-settings" in migrated_project_dict


def test_migration_converts_figure_settings_keys(migrated_project_dict):
    """Test if migrate converts figure-settings keys to hyphen-case."""
    for key in migrated_project_dict["figure-settings"]:
        assert "_" not in key, f"Key '{key}' still uses underscores"


def test_migration_strips_graphs_prefix_from_item_types(migrated_project_dict):
    """Test if migrate removes the 'Graphs' prefix from all item type names."""
    for item in migrated_project_dict["data"]:
        assert not item["type"].startswith("Graphs"), (
            f"Item type '{item['type']}' still has 'Graphs' prefix"
        )


def test_migration_merges_item_data(migrated_project_dict):
    """Test if migrate replaces xdata/ydata keys with a single data tuple."""
    for item in migrated_project_dict["data"]:
        assert "data" in item
        assert "xdata" not in item
        assert "ydata" not in item


def test_migration_preserves_item_count(
    v1_project_dict,
    migrated_project_dict,
):
    """Test if migrate keeps the same number of items as the original."""
    assert (
        len(migrated_project_dict["data"]) == len(v1_project_dict["data"])
    )


def test_migration_preserves_item_names(
    v1_project_dict,
    migrated_project_dict,
):
    """Test if migrate keeps all item names unchanged."""
    original_names = {i["name"] for i in v1_project_dict["data"]}
    migrated_names = {i["name"] for i in migrated_project_dict["data"]}
    assert migrated_names == original_names


def test_migration_result_passes_validation(migrated_project_dict):
    """Test if the migrated dict passes ProjectValidator without errors."""
    ProjectValidator(
        migrated_project_dict,
        Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    ).validate()


def test_validator_constructs_figure_settings(validated_project):
    """Test if validate correctly constructs a FigureSettings object."""
    assert isinstance(
        validated_project.figure_settings, Graphs.FigureSettings,
    )


def test_migration_preserves_item_data(
    v1_project_dict,
    migrated_project_dict,
):
    """Test if migrate preserves data for each item."""
    for legacy, item in zip(
        v1_project_dict["data"],
        migrated_project_dict["data"],
    ):
        xdata, ydata, xerr, yerr = item["data"]
        assert list(xdata) == legacy["xdata"]
        assert list(ydata) == legacy["ydata"]
        assert xerr is None
        assert yerr is None
