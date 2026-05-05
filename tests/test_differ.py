"""Tests for schema diffing logic."""

import pytest

from sqldiff.schema import Column, Schema, Table
from sqldiff.differ import diff_schemas
from sqldiff.formatter import format_text, format_json


def _make_schema(*tables: Table) -> Schema:
    schema = Schema()
    for t in tables:
        schema.add_table(t)
    return schema


def _make_table(name: str, **columns) -> Table:
    table = Table(name=name)
    for col_name, col_type in columns.items():
        table.add_column(Column(name=col_name, data_type=col_type))
    return table


def test_no_changes():
    old = _make_schema(_make_table("users", id="INTEGER", name="TEXT"))
    new = _make_schema(_make_table("users", id="INTEGER", name="TEXT"))
    diff = diff_schemas(old, new)
    assert not diff.has_changes


def test_table_added():
    old = _make_schema(_make_table("users", id="INTEGER"))
    new = _make_schema(_make_table("users", id="INTEGER"), _make_table("orders", id="INTEGER"))
    diff = diff_schemas(old, new)
    assert "orders" in diff.tables_added
    assert not diff.tables_removed


def test_table_removed():
    old = _make_schema(_make_table("users", id="INTEGER"), _make_table("orders", id="INTEGER"))
    new = _make_schema(_make_table("users", id="INTEGER"))
    diff = diff_schemas(old, new)
    assert "orders" in diff.tables_removed
    assert not diff.tables_added


def test_column_added():
    old = _make_schema(_make_table("users", id="INTEGER"))
    new = _make_schema(_make_table("users", id="INTEGER", email="TEXT"))
    diff = diff_schemas(old, new)
    assert "users.email" in diff.columns_added


def test_column_removed():
    old = _make_schema(_make_table("users", id="INTEGER", email="TEXT"))
    new = _make_schema(_make_table("users", id="INTEGER"))
    diff = diff_schemas(old, new)
    assert "users.email" in diff.columns_removed


def test_column_modified():
    old_table = Table(name="users")
    old_table.add_column(Column(name="age", data_type="INTEGER"))
    new_table = Table(name="users")
    new_table.add_column(Column(name="age", data_type="TEXT"))
    diff = diff_schemas(_make_schema(old_table), _make_schema(new_table))
    assert "users.age" in diff.columns_modified


def test_format_text_no_changes():
    diff = diff_schemas(Schema(), Schema())
    assert format_text(diff) == "No schema changes detected."


def test_format_json_structure():
    old = _make_schema(_make_table("users", id="INTEGER"))
    new = _make_schema(_make_table("users", id="INTEGER", name="TEXT"), _make_table("posts", id="INTEGER"))
    diff = diff_schemas(old, new)
    result = format_json(diff)
    assert "tables" in result
    assert "columns" in result
    assert result["has_changes"] is True
    assert "posts" in result["tables"]["added"]
    assert "users.name" in result["columns"]["added"]
