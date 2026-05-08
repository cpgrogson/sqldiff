"""Tests for sqldiff.summarizer."""
import pytest

from sqldiff.differ import SchemaDiff
from sqldiff.comparator import TableDiff, ColumnDiff
from sqldiff.schema import Column, Table, Index
from sqldiff.summarizer import DiffStats, summarize


def _col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def _table(name: str) -> Table:
    return Table(name=name, columns=[_col("id", "INTEGER")], indexes=[])


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(tables_added=[], tables_removed=[], tables_modified=[])


def _table_diff_with_col_change() -> TableDiff:
    old_col = _col("email", "TEXT")
    new_col = _col("email", "VARCHAR(255)")
    col_diff = ColumnDiff(column_name="email", old=old_col, new=new_col)
    return TableDiff(
        table_name="users",
        columns_added=[],
        columns_removed=[],
        columns_modified=[col_diff],
        indexes_added=[],
        indexes_removed=[],
    )


# --- DiffStats ---

def test_total_changes_sums_all_fields():
    stats = DiffStats(tables_added=1, tables_removed=2, columns_added=3)
    assert stats.total_changes == 6


def test_to_dict_contains_all_keys():
    stats = DiffStats(tables_added=1)
    d = stats.to_dict()
    assert "tables_added" in d
    assert "total_changes" in d
    assert d["tables_added"] == 1


def test_str_contains_totals():
    stats = DiffStats(tables_added=2, columns_removed=1)
    text = str(stats)
    assert "Total" in text
    assert "3" in text  # 2 + 1


# --- summarize ---

def test_empty_diff_returns_zero_stats():
    stats = summarize(_empty_diff())
    assert stats.total_changes == 0
    assert stats.tables_added == 0


def test_tables_added_counted():
    diff = SchemaDiff(
        tables_added=[_table("orders"), _table("products")],
        tables_removed=[],
        tables_modified=[],
    )
    stats = summarize(diff)
    assert stats.tables_added == 2
    assert stats.tables_removed == 0


def test_tables_removed_counted():
    diff = SchemaDiff(
        tables_added=[],
        tables_removed=[_table("legacy")],
        tables_modified=[],
    )
    stats = summarize(diff)
    assert stats.tables_removed == 1


def test_modified_table_with_column_change():
    diff = SchemaDiff(
        tables_added=[],
        tables_removed=[],
        tables_modified=[_table_diff_with_col_change()],
    )
    stats = summarize(diff)
    assert stats.tables_modified == 1
    assert stats.columns_modified == 1


def test_index_changes_counted():
    idx = Index(name="idx_email", columns=["email"], unique=False)
    table_diff = TableDiff(
        table_name="users",
        columns_added=[],
        columns_removed=[],
        columns_modified=[],
        indexes_added=[idx],
        indexes_removed=[idx],
    )
    diff = SchemaDiff(tables_added=[], tables_removed=[], tables_modified=[table_diff])
    stats = summarize(diff)
    assert stats.indexes_added == 1
    assert stats.indexes_removed == 1
    assert stats.tables_modified == 1
