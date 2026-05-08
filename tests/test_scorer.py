"""Tests for sqldiff.scorer."""
import pytest

from sqldiff.schema import Column, Index, Schema, Table
from sqldiff.differ import diff_schemas
from sqldiff.scorer import SimilarityScore, _count_changes, _count_objects, score_schemas


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def _table(name: str, cols=None) -> Table:
    cols = cols or [_col("id", "INTEGER")]
    return Table(name=name, columns=cols, indexes=[])


def _schema(*tables: Table) -> Schema:
    return Schema(tables={t.name: t for t in tables})


# ---------------------------------------------------------------------------
# SimilarityScore
# ---------------------------------------------------------------------------

def test_score_identical_schemas():
    s = _schema(_table("users"), _table("posts"))
    diff = diff_schemas(s, s)
    result = score_schemas(s, s, diff)
    assert result.score == 1.0
    assert result.changed_objects == 0
    assert result.total_objects == 2


def test_score_completely_different_schemas():
    old = _schema(*[_table(f"t{i}") for i in range(5)])
    new = _schema(*[_table(f"x{i}") for i in range(5)])
    diff = diff_schemas(old, new)
    result = score_schemas(old, new, diff)
    # 5 removed + 5 added = 10 changes over 10 objects -> score = 0.0
    assert result.score == 0.0
    assert result.changed_objects == 10


def test_score_partial_change():
    old = _schema(_table("users"), _table("posts"))
    new = _schema(_table("users"), _table("comments"))
    diff = diff_schemas(old, new)
    result = score_schemas(old, new, diff)
    # 1 removed + 1 added = 2 changes over 3 unique tables
    assert result.total_objects == 3
    assert result.changed_objects == 2
    assert 0.0 < result.score < 1.0


def test_score_clamped_to_zero():
    """More changes than objects should not produce a negative score."""
    old = _schema(_table("a"))
    new = _schema(
        _table("b"),
        _table("c"),
        _table("d"),
        _table("e"),
    )
    diff = diff_schemas(old, new)
    result = score_schemas(old, new, diff)
    assert result.score >= 0.0


# ---------------------------------------------------------------------------
# _count_changes
# ---------------------------------------------------------------------------

def test_count_changes_empty_diff():
    s = _schema(_table("t"))
    diff = diff_schemas(s, s)
    assert _count_changes(diff) == 0


def test_count_changes_added_table():
    old = _schema(_table("a"))
    new = _schema(_table("a"), _table("b"))
    diff = diff_schemas(old, new)
    assert _count_changes(diff) == 1


# ---------------------------------------------------------------------------
# _count_objects
# ---------------------------------------------------------------------------

def test_count_objects_union():
    old = _schema(_table("a"), _table("b"))
    new = _schema(_table("b"), _table("c"))
    assert _count_objects(old, new) == 3


def test_count_objects_minimum_one():
    """Empty schemas should not cause division by zero."""
    empty = Schema(tables={})
    assert _count_objects(empty, empty) == 1
