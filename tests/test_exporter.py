"""Tests for sqldiff.exporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqldiff.differ import SchemaDiff
from sqldiff.exporter import export_diff, SUPPORTED_FORMATS
from sqldiff.schema import Column, Index


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_diff() -> SchemaDiff:
    return SchemaDiff(
        tables_added=[],
        tables_removed=[],
        tables_changed={},
    )


def _rich_diff() -> SchemaDiff:
    col = Column(name="email", col_type="TEXT", nullable=True, default=None)
    idx = Index(name="idx_email", columns=["email"], unique=True)
    return SchemaDiff(
        tables_added=["users"],
        tables_removed=["legacy"],
        tables_changed={
            "orders": {
                "columns_added": [col],
                "columns_removed": [],
                "columns_changed": {"status": {"col_type": ("INT", "TEXT")}},
                "indexes_added": [idx],
                "indexes_removed": [],
            }
        },
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_supported_formats():
    assert set(SUPPORTED_FORMATS) == {"text", "json", "sql"}


def test_export_text_creates_file(tmp_path):
    dest = tmp_path / "out.txt"
    result = export_diff(_empty_diff(), dest, fmt="text")
    assert result == dest
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") != ""


def test_export_json_valid_json(tmp_path):
    dest = tmp_path / "out.json"
    export_diff(_rich_diff(), dest, fmt="json")
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert "tables_added" in data
    assert "users" in data["tables_added"]


def test_export_sql_contains_drop(tmp_path):
    dest = tmp_path / "out.sql"
    export_diff(_rich_diff(), dest, fmt="sql")
    content = dest.read_text(encoding="utf-8")
    assert "DROP TABLE IF EXISTS legacy" in content


def test_export_sql_contains_add_column(tmp_path):
    dest = tmp_path / "out.sql"
    export_diff(_rich_diff(), dest, fmt="sql")
    content = dest.read_text(encoding="utf-8")
    assert "ADD COLUMN email" in content


def test_export_sql_contains_create_index(tmp_path):
    dest = tmp_path / "out.sql"
    export_diff(_rich_diff(), dest, fmt="sql")
    content = dest.read_text(encoding="utf-8")
    assert "CREATE UNIQUE INDEX idx_email" in content


def test_export_creates_parent_dirs(tmp_path):
    dest = tmp_path / "nested" / "dir" / "out.txt"
    export_diff(_empty_diff(), dest, fmt="text")
    assert dest.exists()


def test_export_invalid_format_raises(tmp_path):
    with pytest.raises(ValueError, match="Unsupported format"):
        export_diff(_empty_diff(), tmp_path / "out.xyz", fmt="xml")


def test_export_returns_path_object(tmp_path):
    dest = str(tmp_path / "out.txt")
    result = export_diff(_empty_diff(), dest, fmt="text")
    assert isinstance(result, Path)
