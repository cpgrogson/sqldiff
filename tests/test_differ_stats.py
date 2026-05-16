"""Tests for sqldiff.differ_stats."""
from __future__ import annotations

import pytest

from sqldiff.schema import Column, Index, Table, Schema
from sqldiff.differ import SchemaDiff, diff_schemas
from sqldiff.differ_stats import TableStats, DiffStatReport, build_stat_report


def _col(name: str, col_type: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable, default=None)


def _table(name: str, columns=(), indexes=()) -> Table:
    return Table(name=name, columns=list(columns), indexes=list(indexes))


def _schema(*tables) -> Schema:
    return Schema(tables={t.name: t for t in tables})


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(tables_added=[], tables_removed=[], tables_modified={})


# ── TableStats ────────────────────────────────────────────────────────────────

def test_table_stats_total_sums_all_fields():
    ts = TableStats(name="t", columns_added=2, columns_removed=1, indexes_added=1)
    assert ts.total == 4


def test_table_stats_to_dict_keys():
    ts = TableStats(name="users", columns_added=1)
    d = ts.to_dict()
    assert d["table"] == "users"
    assert d["total"] == 1
    assert "columns_added" in d


# ── DiffStatReport ────────────────────────────────────────────────────────────

def test_diff_stat_report_total_changes_empty():
    r = DiffStatReport()
    assert r.total_changes == 0


def test_diff_stat_report_total_changes_tables():
    r = DiffStatReport(tables_added=["a", "b"], tables_removed=["c"])
    assert r.total_changes == 3


def test_diff_stat_report_total_changes_includes_table_stats():
    ts = TableStats(name="x", columns_added=3)
    r = DiffStatReport(table_stats=[ts])
    assert r.total_changes == 3


def test_diff_stat_report_str_no_changes():
    r = DiffStatReport()
    assert "0" in str(r)


def test_diff_stat_report_str_lists_added_tables():
    r = DiffStatReport(tables_added=["orders"])
    assert "orders" in str(r)


def test_diff_stat_report_to_dict_structure():
    r = DiffStatReport(tables_added=["a"])
    d = r.to_dict()
    assert "tables_added" in d
    assert "tables_removed" in d
    assert "table_changes" in d
    assert "total_changes" in d


# ── build_stat_report ─────────────────────────────────────────────────────────

def test_build_stat_report_empty_diff():
    r = build_stat_report(_empty_diff())
    assert r.total_changes == 0
    assert r.tables_added == []
    assert r.tables_removed == []


def test_build_stat_report_tables_added():
    before = _schema()
    after = _schema(_table("users", [_col("id")]))
    diff = diff_schemas(before, after)
    r = build_stat_report(diff)
    assert "users" in r.tables_added


def test_build_stat_report_tables_removed():
    before = _schema(_table("orders", [_col("id")]))
    after = _schema()
    diff = diff_schemas(before, after)
    r = build_stat_report(diff)
    assert "orders" in r.tables_removed


def test_build_stat_report_column_changes():
    before = _schema(_table("t", [_col("a"), _col("b")]))
    after = _schema(_table("t", [_col("a"), _col("c")]))
    diff = diff_schemas(before, after)
    r = build_stat_report(diff)
    assert len(r.table_stats) == 1
    ts = r.table_stats[0]
    assert ts.name == "t"
    assert ts.columns_added == 1
    assert ts.columns_removed == 1
