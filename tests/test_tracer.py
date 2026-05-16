"""Tests for sqldiff.tracer."""
from __future__ import annotations

import pytest

from sqldiff.schema import Column, Table, Schema
from sqldiff.tracer import ColumnLineage, TraceReport, trace_column, trace_schema


def _col(name: str, typ: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, type=typ, nullable=nullable, default=None)


def _table(name: str, cols: list) -> Table:
    return Table(name=name, columns={c.name: c for c in cols}, indexes={})


def _schema(*tables: Table) -> Schema:
    return Schema(tables={t.name: t for t in tables})


def _snap(label: str, schema: Schema) -> dict:
    return {label: schema}


# ---------------------------------------------------------------------------
# ColumnLineage
# ---------------------------------------------------------------------------

def test_column_lineage_str():
    ln = ColumnLineage(table="users", column="email", history=[{}, {}])
    assert "users.email" in str(ln)
    assert "2 snapshot" in str(ln)


def test_column_lineage_added_in():
    ln = ColumnLineage(
        table="users", column="email",
        history=[
            {"snapshot": "v1", "status": "added"},
            {"snapshot": "v2", "status": "unchanged"},
        ],
    )
    assert ln.added_in() == "v1"
    assert ln.removed_in() is None


def test_column_lineage_removed_in():
    ln = ColumnLineage(
        table="users", column="email",
        history=[
            {"snapshot": "v1", "status": "unchanged"},
            {"snapshot": "v2", "status": "removed"},
        ],
    )
    assert ln.removed_in() == "v2"
    assert ln.added_in() is None


# ---------------------------------------------------------------------------
# TraceReport
# ---------------------------------------------------------------------------

def test_trace_report_empty():
    r = TraceReport()
    assert r.is_empty()
    assert "no lineage" in str(r)


def test_trace_report_for_table():
    ln1 = ColumnLineage(table="users", column="id", history=[])
    ln2 = ColumnLineage(table="orders", column="id", history=[])
    r = TraceReport(lineages=[ln1, ln2])
    assert r.for_table("users") == [ln1]
    assert r.for_table("orders") == [ln2]
    assert r.for_table("missing") == []


# ---------------------------------------------------------------------------
# trace_column
# ---------------------------------------------------------------------------

def test_trace_column_stable():
    col = _col("id", "INTEGER")
    s = _schema(_table("users", [col]))
    snaps = [_snap("v1", s), _snap("v2", s)]
    ln = trace_column(snaps, "users", "id")
    statuses = [e["status"] for e in ln.history]
    assert statuses == ["added", "unchanged"]


def test_trace_column_added_then_removed():
    s1 = _schema(_table("users", []))
    s2 = _schema(_table("users", [_col("email")]))
    s3 = _schema(_table("users", []))
    snaps = [_snap("v1", s1), _snap("v2", s2), _snap("v3", s3)]
    ln = trace_column(snaps, "users", "email")
    statuses = [e["status"] for e in ln.history]
    assert statuses == ["unchanged", "added", "removed"]


def test_trace_column_modified():
    s1 = _schema(_table("users", [_col("score", "INTEGER")]))
    s2 = _schema(_table("users", [_col("score", "REAL")]))
    snaps = [_snap("v1", s1), _snap("v2", s2)]
    ln = trace_column(snaps, "users", "score")
    assert ln.history[1]["status"] == "modified"


# ---------------------------------------------------------------------------
# trace_schema
# ---------------------------------------------------------------------------

def test_trace_schema_finds_all_columns():
    s1 = _schema(_table("users", [_col("id"), _col("name")]))
    s2 = _schema(_table("users", [_col("id"), _col("email")]))
    snaps = [_snap("v1", s1), _snap("v2", s2)]
    report = trace_schema(snaps)
    col_keys = {(ln.table, ln.column) for ln in report.lineages}
    assert ("users", "id") in col_keys
    assert ("users", "name") in col_keys
    assert ("users", "email") in col_keys


def test_trace_schema_empty_snapshots():
    report = trace_schema([])
    assert report.is_empty()
