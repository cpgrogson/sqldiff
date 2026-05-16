"""Tests for sqldiff.archiver."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqldiff.archiver import (
    ArchiveEntry,
    archive_diff,
    list_archives,
    load_archive,
)
from sqldiff.differ import SchemaDiff
from sqldiff.schema import Column, Table


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def _table(name: str) -> Table:
    return Table(name=name, columns=[_col("id", "INTEGER")], indexes=[])


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(added=[], removed=[], modified=[])


def _rich_diff() -> SchemaDiff:
    return SchemaDiff(
        added=[_table("orders")],
        removed=[_table("legacy")],
        modified=[],
    )


# ---------------------------------------------------------------------------
# ArchiveEntry.__str__
# ---------------------------------------------------------------------------

def test_archive_entry_str_with_label():
    entry = ArchiveEntry(
        archive_id="20240101T000000Z",
        created_at="20240101T000000Z",
        label="release-1.0",
        tables_added=1,
        tables_removed=0,
        tables_modified=2,
    )
    text = str(entry)
    assert "release-1.0" in text
    assert "+1" in text
    assert "-0" in text
    assert "~2" in text


def test_archive_entry_str_without_label():
    entry = ArchiveEntry(
        archive_id="20240101T000000Z",
        created_at="20240101T000000Z",
        label=None,
        tables_added=0,
        tables_removed=0,
        tables_modified=0,
    )
    assert "[" not in str(entry)


# ---------------------------------------------------------------------------
# archive_diff
# ---------------------------------------------------------------------------

def test_archive_diff_creates_json_file(tmp_path: Path):
    diff = _empty_diff()
    entry = archive_diff(diff, tmp_path)
    diff_file = tmp_path / f"{entry.archive_id}.json"
    assert diff_file.exists()


def test_archive_diff_json_is_valid(tmp_path: Path):
    diff = _rich_diff()
    entry = archive_diff(diff, tmp_path)
    raw = (tmp_path / f"{entry.archive_id}.json").read_text()
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)


def test_archive_diff_updates_index(tmp_path: Path):
    archive_diff(_empty_diff(), tmp_path)
    archive_diff(_empty_diff(), tmp_path)
    entries = list_archives(tmp_path)
    assert len(entries) == 2


def test_archive_diff_records_counts(tmp_path: Path):
    diff = _rich_diff()
    entry = archive_diff(diff, tmp_path)
    assert entry.tables_added == 1
    assert entry.tables_removed == 1
    assert entry.tables_modified == 0


def test_archive_diff_stores_label(tmp_path: Path):
    entry = archive_diff(_empty_diff(), tmp_path, label="v2")
    assert entry.label == "v2"
    reloaded = list_archives(tmp_path)
    assert reloaded[0].label == "v2"


def test_archive_diff_creates_directory(tmp_path: Path):
    target = tmp_path / "nested" / "archive"
    archive_diff(_empty_diff(), target)
    assert target.is_dir()


# ---------------------------------------------------------------------------
# list_archives
# ---------------------------------------------------------------------------

def test_list_archives_empty_directory(tmp_path: Path):
    assert list_archives(tmp_path) == []


def test_list_archives_newest_first(tmp_path: Path):
    e1 = archive_diff(_empty_diff(), tmp_path, label="first")
    e2 = archive_diff(_empty_diff(), tmp_path, label="second")
    entries = list_archives(tmp_path)
    assert entries[0].archive_id == e2.archive_id
    assert entries[1].archive_id == e1.archive_id


# ---------------------------------------------------------------------------
# load_archive
# ---------------------------------------------------------------------------

def test_load_archive_returns_json_string(tmp_path: Path):
    entry = archive_diff(_rich_diff(), tmp_path)
    raw = load_archive(tmp_path, entry.archive_id)
    assert isinstance(raw, str)
    json.loads(raw)  # must be valid JSON


def test_load_archive_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_archive(tmp_path, "nonexistent")
