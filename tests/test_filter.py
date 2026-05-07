"""Tests for sqldiff.filter."""

from __future__ import annotations

import pytest

from sqldiff.schema import Schema, Table, Column
from sqldiff.differ import SchemaDiff
from sqldiff.filter import FilterOptions, filter_schema, filter_diff


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _col(name: str = "id", type_: str = "INTEGER") -> Column:
    return Column(name=name, type=type_, nullable=True, default=None)


def _table(name: str) -> Table:
    return Table(name=name, columns=[_col()], indexes=[])


def _schema(*names: str) -> Schema:
    return Schema(tables={n: _table(n) for n in names})


def _diff() -> SchemaDiff:
    return SchemaDiff(
        added={"orders": _table("orders"), "audit_log": _table("audit_log")},
        removed={"legacy": _table("legacy")},
        modified={},
    )


# ---------------------------------------------------------------------------
# FilterOptions.matches
# ---------------------------------------------------------------------------

def test_matches_no_rules_accepts_all():
    opts = FilterOptions()
    assert opts.matches("users") is True


def test_matches_include_pattern():
    opts = FilterOptions(include=["order*"])
    assert opts.matches("orders") is True
    assert opts.matches("users") is False


def test_matches_exclude_pattern():
    opts = FilterOptions(exclude=["audit_*"])
    assert opts.matches("users") is True
    assert opts.matches("audit_log") is False


def test_matches_include_and_exclude():
    opts = FilterOptions(include=["order*"], exclude=["order_archive"])
    assert opts.matches("orders") is True
    assert opts.matches("order_archive") is False
    assert opts.matches("users") is False


# ---------------------------------------------------------------------------
# filter_schema
# ---------------------------------------------------------------------------

def test_filter_schema_no_rules_returns_all():
    schema = _schema("users", "orders", "products")
    result = filter_schema(schema, FilterOptions())
    assert set(result.tables.keys()) == {"users", "orders", "products"}


def test_filter_schema_include():
    schema = _schema("users", "orders", "audit_log")
    result = filter_schema(schema, FilterOptions(include=["audit_*"]))
    assert set(result.tables.keys()) == {"audit_log"}


def test_filter_schema_exclude():
    schema = _schema("users", "orders", "audit_log")
    result = filter_schema(schema, FilterOptions(exclude=["audit_*"]))
    assert "audit_log" not in result.tables
    assert "users" in result.tables


def test_filter_schema_does_not_mutate_original():
    schema = _schema("users", "audit_log")
    filter_schema(schema, FilterOptions(exclude=["audit_*"]))
    assert "audit_log" in schema.tables


# ---------------------------------------------------------------------------
# filter_diff
# ---------------------------------------------------------------------------

def test_filter_diff_no_rules_keeps_all():
    diff = _diff()
    result = filter_diff(diff, FilterOptions())
    assert set(result.added.keys()) == {"orders", "audit_log"}
    assert set(result.removed.keys()) == {"legacy"}


def test_filter_diff_exclude_audit():
    diff = _diff()
    result = filter_diff(diff, FilterOptions(exclude=["audit_*"]))
    assert "audit_log" not in result.added
    assert "orders" in result.added


def test_filter_diff_include_only_orders():
    diff = _diff()
    result = filter_diff(diff, FilterOptions(include=["order*"]))
    assert set(result.added.keys()) == {"orders"}
    assert result.removed == {}
