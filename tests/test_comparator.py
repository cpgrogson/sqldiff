"""Tests for sqldiff.comparator module."""

import pytest

from sqldiff.comparator import ColumnDiff, IndexDiff, TableComparison, compare_tables
from sqldiff.schema import Column, Index, Table


def _col(name, type_="TEXT", nullable=True, default=None):
    return Column(name=name, type=type_, nullable=nullable, default=default)


def _idx(name, columns=None, unique=False):
    return Index(name=name, columns=columns or ["id"], unique=unique)


def _table(name, columns=None, indexes=None):
    return Table(name=name, columns=columns or [], indexes=indexes or [])


# --- ColumnDiff ---

def test_column_diff_no_changes():
    c = _col("email")
    diff = ColumnDiff(name="email", old=c, new=c)
    assert not diff.has_changes
    assert diff.changes == []


def test_column_diff_type_change():
    diff = ColumnDiff(name="age", old=_col("age", "INT"), new=_col("age", "BIGINT"))
    assert diff.has_changes
    assert any("type" in c for c in diff.changes)


def test_column_diff_nullable_change():
    diff = ColumnDiff(name="x", old=_col("x", nullable=True), new=_col("x", nullable=False))
    assert diff.has_changes
    assert any("nullable" in c for c in diff.changes)


def test_column_diff_default_change():
    diff = ColumnDiff(name="x", old=_col("x", default=None), new=_col("x", default="0"))
    assert diff.has_changes
    assert any("default" in c for c in diff.changes)


def test_column_diff_multiple_changes():
    diff = ColumnDiff(
        name="x",
        old=_col("x", type_="INT", nullable=True),
        new=_col("x", type_="TEXT", nullable=False),
    )
    assert len(diff.changes) == 2


# --- IndexDiff ---

def test_index_diff_no_changes():
    i = _idx("idx_id")
    diff = IndexDiff(name="idx_id", old=i, new=i)
    assert not diff.has_changes


def test_index_diff_unique_change():
    diff = IndexDiff(
        name="idx",
        old=_idx("idx", unique=False),
        new=_idx("idx", unique=True),
    )
    assert diff.has_changes
    assert any("unique" in c for c in diff.changes)


def test_index_diff_columns_change():
    diff = IndexDiff(
        name="idx",
        old=_idx("idx", columns=["a"]),
        new=_idx("idx", columns=["a", "b"]),
    )
    assert diff.has_changes


# --- compare_tables ---

def test_compare_tables_no_changes():
    t = _table("users", columns=[_col("id")], indexes=[_idx("pk")])
    result = compare_tables(t, t)
    assert not result.has_changes


def test_compare_tables_added_column():
    old = _table("users", columns=[_col("id")])
    new = _table("users", columns=[_col("id"), _col("email")])
    result = compare_tables(old, new)
    assert len(result.added_columns) == 1
    assert result.added_columns[0].name == "email"


def test_compare_tables_removed_column():
    old = _table("users", columns=[_col("id"), _col("email")])
    new = _table("users", columns=[_col("id")])
    result = compare_tables(old, new)
    assert len(result.removed_columns) == 1
    assert result.removed_columns[0].name == "email"


def test_compare_tables_modified_column():
    old = _table("users", columns=[_col("id", type_="INT")])
    new = _table("users", columns=[_col("id", type_="BIGINT")])
    result = compare_tables(old, new)
    assert len(result.modified_columns) == 1
    assert result.has_changes


def test_compare_tables_added_index():
    old = _table("users", columns=[_col("id")])
    new = _table("users", columns=[_col("id")], indexes=[_idx("idx_id")])
    result = compare_tables(old, new)
    assert len(result.added_indexes) == 1


def test_compare_tables_removed_index():
    old = _table("users", columns=[_col("id")], indexes=[_idx("idx_id")])
    new = _table("users", columns=[_col("id")])
    result = compare_tables(old, new)
    assert len(result.removed_indexes) == 1
