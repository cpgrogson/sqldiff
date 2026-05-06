"""Tests for sqldiff.snapshotter."""

import os
import pytest

from sqldiff.snapshotter import (
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)

_SQL = """
CREATE TABLE users (
    id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT
);
"""

_SQL2 = """
CREATE TABLE orders (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL
);
"""


def test_save_creates_file(tmp_path):
    path = save_snapshot(str(tmp_path), "v1", _SQL)
    assert os.path.isfile(path)
    assert path.endswith(".snap.json")


def test_save_creates_directory(tmp_path):
    snap_dir = str(tmp_path / "snapshots" / "nested")
    save_snapshot(snap_dir, "v1", _SQL)
    assert os.path.isdir(snap_dir)


def test_load_returns_schema(tmp_path):
    save_snapshot(str(tmp_path), "v1", _SQL)
    schema = load_snapshot(str(tmp_path), "v1")
    assert "users" in schema.tables
    assert len(schema.tables["users"].columns) == 3


def test_load_missing_snapshot_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="v99"):
        load_snapshot(str(tmp_path), "v99")


def test_list_empty_directory(tmp_path):
    assert list_snapshots(str(tmp_path)) == []


def test_list_nonexistent_directory(tmp_path):
    missing = str(tmp_path / "no_such_dir")
    assert list_snapshots(missing) == []


def test_list_returns_metadata(tmp_path):
    save_snapshot(str(tmp_path), "alpha", _SQL)
    save_snapshot(str(tmp_path), "beta", _SQL2)
    metas = list_snapshots(str(tmp_path))
    names = [m.name for m in metas]
    assert "alpha" in names
    assert "beta" in names
    assert len(metas) == 2


def test_list_metadata_has_created_at(tmp_path):
    save_snapshot(str(tmp_path), "v1", _SQL)
    metas = list_snapshots(str(tmp_path))
    assert metas[0].created_at  # non-empty ISO timestamp


def test_delete_existing_snapshot(tmp_path):
    save_snapshot(str(tmp_path), "v1", _SQL)
    result = delete_snapshot(str(tmp_path), "v1")
    assert result is True
    assert list_snapshots(str(tmp_path)) == []


def test_delete_missing_snapshot_returns_false(tmp_path):
    result = delete_snapshot(str(tmp_path), "ghost")
    assert result is False


def test_roundtrip_multiple_tables(tmp_path):
    sql = _SQL + _SQL2
    save_snapshot(str(tmp_path), "combined", sql)
    schema = load_snapshot(str(tmp_path), "combined")
    assert "users" in schema.tables
    assert "orders" in schema.tables
