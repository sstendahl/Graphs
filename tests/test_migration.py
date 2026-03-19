# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for project migration."""
import json
import os

from gi.repository import Gio, Graphs

from graphs.project import ProjectMigrator, read_project_file

PROJECTFILE_V1 = "project_v1.graphs"


def _load_legacy():
    """Load the legacy v1 project dict from the test fixture."""
    with open(PROJECTFILE_V1) as f:
        return json.load(f)


def test_migration_completes_without_error():
    """Test if migrate returns a dict with the expected top-level keys."""
    result = ProjectMigrator(
        _load_legacy(), Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    ).migrate()
    assert "data" in result
    assert "figure-settings" in result


def test_migration_converts_figure_settings_keys():
    """Test if migrate converts figure-settings keys to hyphen-case."""
    result = ProjectMigrator(
        _load_legacy(), Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    ).migrate()
    for key in result["figure-settings"]:
        assert "_" not in key, f"Key '{key}' still uses underscores"


def test_migration_strips_graphs_prefix_from_item_types():
    """Test if migrate removes the 'Graphs' prefix from all item type names."""
    result = ProjectMigrator(
        _load_legacy(), Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    ).migrate()
    for item in result["data"]:
        assert not item["type"].startswith("Graphs"), (
            f"Item type '{item['type']}' still has 'Graphs' prefix"
        )


def test_migration_merges_item_data():
    """Test if migrate replaces xdata/ydata keys with a single data tuple."""
    result = ProjectMigrator(
        _load_legacy(), Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    ).migrate()
    for item in result["data"]:
        assert "data" in item
        assert "xdata" not in item
        assert "ydata" not in item


def test_migration_preserves_item_names():
    """Test if migrate keeps all item names unchanged."""
    original_names = {i["name"] for i in _load_legacy()["data"]}
    result = ProjectMigrator(
        _load_legacy(), Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    ).migrate()
    migrated_names = {i["name"] for i in result["data"]}
    assert migrated_names == original_names


def test_migration_preserves_item_count():
    """Test if migrate keeps the same number of items as the original."""
    legacy = _load_legacy()
    result = ProjectMigrator(
        legacy, Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    ).migrate()
    assert len(result["data"]) == len(legacy["data"])


def test_read_legacy_project_file():
    """Test if read_project_file reads the legacy.graphs fixture."""
    file = Gio.File.new_for_path(PROJECTFILE_V1)
    result = read_project_file(
        file, Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    )
    assert "data" in result
    assert "figure-settings" in result


def test_read_legacy_project_figure_settings():
    """Test if read_project_file preserves figure-settings from legacy file."""
    file = Gio.File.new_for_path(PROJECTFILE_V1)
    result = read_project_file(
        file, Graphs.ProjectParseFlags.ALLOW_LEGACY_MIGRATION,
    )
    fs = result["figure-settings"]
    assert fs["bottom-label"] == "bottomx"
    assert fs["left-label"] == "lefty"
    assert fs["right-label"] == "righty"
    assert fs["top-label"] == "topx"
    assert fs["title"] == "title"
