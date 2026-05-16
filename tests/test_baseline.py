"""Tests for sqldiff.baseline."""
import json
import pytest

from sqldiff.baseline import (
    BaselineMeta,
    save_baseline,
    load_baseline,
    diff_from_baseline,
)
from sqldiff.differ import SchemaDiff
from sqldiff.schema import Schema, Table, Column


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def _table(name: str) -> Table:
    return Table(name=name, columns=[_col("id", "INTEGER")], indexes=[])


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables={})


def _rich_diff() -> SchemaDiff:
    return SchemaDiff(
        added_tables=["orders", "products"],
        removed_tables=["legacy"],
        modified_tables={"users": object()},  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# BaselineMeta
# ---------------------------------------------------------------------------

def test_baseline_meta_str_with_label():
    meta = BaselineMeta(
        created_at="2024-01-01T00:00:00+00:00",
        label="v1",
        added_tables=[],
        removed_tables=[],
        modified_tables=[],
    )
    assert "v1" in str(meta)
    assert "2024-01-01" in str(meta)


def test_baseline_meta_str_without_label():
    meta = BaselineMeta(
        created_at="2024-06-15T12:00:00+00:00",
        label=None,
        added_tables=[],
        removed_tables=[],
        modified_tables=[],
    )
    result = str(meta)
    assert "Baseline(" in result
    assert "label" not in result


def test_baseline_meta_round_trip():
    original = BaselineMeta(
        created_at="2024-01-01T00:00:00+00:00",
        label="release",
        added_tables=["a"],
        removed_tables=["b"],
        modified_tables=["c"],
    )
    restored = BaselineMeta.from_dict(original.to_dict())
    assert restored.label == original.label
    assert restored.added_tables == ["a"]
    assert restored.removed_tables == ["b"]
    assert restored.modified_tables == ["c"]


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path):
    meta = save_baseline(_rich_diff(), str(tmp_path))
    assert (tmp_path / ".sqldiff_baseline.json").exists()
    assert isinstance(meta.created_at, str)


def test_save_stores_label(tmp_path):
    save_baseline(_rich_diff(), str(tmp_path), label="sprint-42")
    data = json.loads((tmp_path / ".sqldiff_baseline.json").read_text())
    assert data["label"] == "sprint-42"


def test_save_sorts_table_names(tmp_path):
    save_baseline(_rich_diff(), str(tmp_path))
    data = json.loads((tmp_path / ".sqldiff_baseline.json").read_text())
    assert data["added_tables"] == sorted(data["added_tables"])


def test_load_returns_baseline_meta(tmp_path):
    save_baseline(_rich_diff(), str(tmp_path), label="test")
    meta = load_baseline(str(tmp_path))
    assert isinstance(meta, BaselineMeta)
    assert meta.label == "test"
    assert "orders" in meta.added_tables


def test_load_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_baseline(str(tmp_path))


# ---------------------------------------------------------------------------
# diff_from_baseline
# ---------------------------------------------------------------------------

def test_diff_from_baseline_no_drift(tmp_path):
    diff = _rich_diff()
    save_baseline(diff, str(tmp_path))
    result = diff_from_baseline(diff, str(tmp_path))
    assert result["new_added"] == []
    assert result["new_removed"] == []
    assert result["new_modified"] == []


def test_diff_from_baseline_detects_new_table(tmp_path):
    save_baseline(_empty_diff(), str(tmp_path))
    diff = SchemaDiff(added_tables=["invoices"], removed_tables=[], modified_tables={})
    result = diff_from_baseline(diff, str(tmp_path))
    assert "invoices" in result["new_added"]


def test_diff_from_baseline_detects_new_removal(tmp_path):
    save_baseline(_empty_diff(), str(tmp_path))
    diff = SchemaDiff(added_tables=[], removed_tables=["old_table"], modified_tables={})
    result = diff_from_baseline(diff, str(tmp_path))
    assert "old_table" in result["new_removed"]
