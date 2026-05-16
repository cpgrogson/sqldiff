"""Tests for sqldiff.profiler and sqldiff.profile_cli."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from sqldiff.schema import Column, Index, Schema, Table
from sqldiff.profiler import profile_schema, _profile_table
from sqldiff.profile_cli import build_profile_parser, main


def _col(name: str, col_type: str = "TEXT", nullable: bool = True, default=None) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable, default=default)


def _table(name: str, cols=None, indexes=None) -> Table:
    return Table(
        name=name,
        columns=cols or [],
        indexes=indexes or [],
    )


def _schema(*tables: Table) -> Schema:
    return Schema(tables={t.name: t for t in tables})


# ---------------------------------------------------------------------------
# profiler unit tests
# ---------------------------------------------------------------------------

def test_profile_empty_schema():
    p = profile_schema(_schema())
    assert p.table_count == 0
    assert p.total_columns == 0
    assert p.total_indexes == 0
    assert p.tables == []


def test_profile_single_table_column_count():
    t = _table("users", cols=[_col("id", "INT"), _col("name", "TEXT")])
    p = profile_schema(_schema(t))
    assert p.table_count == 1
    assert p.total_columns == 2


def test_profile_table_nullable_columns():
    t = _table("users", cols=[
        _col("id", nullable=False),
        _col("email", nullable=True),
    ])
    tp = _profile_table(t)
    assert tp.nullable_columns == ["email"]


def test_profile_table_columns_with_defaults():
    t = _table("cfg", cols=[
        _col("key", default=None),
        _col("val", default="''"),
    ])
    tp = _profile_table(t)
    assert tp.columns_with_defaults == ["val"]


def test_profile_table_type_counts():
    t = _table("x", cols=[
        _col("a", "int"),
        _col("b", "INT"),
        _col("c", "text"),
    ])
    tp = _profile_table(t)
    assert tp.column_types["INT"] == 2
    assert tp.column_types["TEXT"] == 1


def test_profile_to_dict_keys():
    t = _table("t", cols=[_col("id")])
    p = profile_schema(_schema(t))
    d = p.to_dict()
    assert set(d.keys()) == {"table_count", "total_columns", "total_indexes", "tables"}


def test_profile_str_contains_table_name():
    t = _table("orders", cols=[_col("id")])
    p = profile_schema(_schema(t))
    assert "orders" in str(p)


# ---------------------------------------------------------------------------
# profile_cli tests
# ---------------------------------------------------------------------------

def test_build_profile_parser_defaults():
    parser = build_profile_parser()
    args = parser.parse_args(["schema.sql"])
    assert args.schema == "schema.sql"
    assert args.format == "text"
    assert args.table is None


def test_main_missing_file_exits(tmp_path):
    rc = main([str(tmp_path / "missing.sql")])
    assert rc == 2


def test_main_text_output(tmp_path):
    sql = "CREATE TABLE users (id INT NOT NULL, name TEXT);"
    f = tmp_path / "s.sql"
    f.write_text(sql)
    rc = main([str(f)])
    assert rc == 0


def test_main_json_output(tmp_path, capsys):
    sql = "CREATE TABLE items (sku TEXT NOT NULL);"
    f = tmp_path / "s.sql"
    f.write_text(sql)
    rc = main([str(f), "--format", "json"])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["table_count"] == 1


def test_main_table_filter(tmp_path, capsys):
    sql = "CREATE TABLE users (id INT NOT NULL);"
    f = tmp_path / "s.sql"
    f.write_text(sql)
    rc = main([str(f), "--table", "users"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "users" in out


def test_main_table_filter_missing(tmp_path):
    sql = "CREATE TABLE users (id INT NOT NULL);"
    f = tmp_path / "s.sql"
    f.write_text(sql)
    rc = main([str(f), "--table", "nonexistent"])
    assert rc == 1
