"""Tests for sqldiff.inspector and sqldiff.inspect_cli."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqldiff.schema import Column, Index, Schema, Table
from sqldiff.inspector import inspect_schema, _inspect_table, TableInspection


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _col(name: str, col_type: str = "TEXT", nullable: bool = True, default=None) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable, default=default)


def _idx(name: str, unique: bool = False) -> Index:
    return Index(name=name, columns=["id"], unique=unique)


def _table(name: str, cols=(), idxs=()) -> Table:
    return Table(name=name, columns=list(cols), indexes=list(idxs))


def _schema(*tables: Table) -> Schema:
    return Schema(tables={t.name: t for t in tables})


# ---------------------------------------------------------------------------
# TableInspection
# ---------------------------------------------------------------------------

def test_inspect_table_column_count():
    t = _table("users", cols=[_col("id"), _col("name")])
    ti = _inspect_table(t)
    assert ti.column_count == 2


def test_inspect_table_nullable_columns():
    t = _table("users", cols=[_col("id", nullable=False), _col("bio", nullable=True)])
    ti = _inspect_table(t)
    assert ti.nullable_columns == ["bio"]


def test_inspect_table_columns_with_defaults():
    t = _table("cfg", cols=[_col("flag", default="0"), _col("val")])
    ti = _inspect_table(t)
    assert ti.columns_with_defaults == ["flag"]


def test_inspect_table_has_primary_key_via_unique_index():
    t = _table("users", cols=[_col("id")], idxs=[_idx("pk_users", unique=True)])
    ti = _inspect_table(t)
    assert ti.has_primary_key is True


def test_inspect_table_no_primary_key():
    t = _table("logs", cols=[_col("msg")])
    ti = _inspect_table(t)
    assert ti.has_primary_key is False


def test_inspect_table_to_dict_keys():
    t = _table("x", cols=[_col("a")])
    d = _inspect_table(t).to_dict()
    assert set(d.keys()) == {
        "name", "column_count", "index_count",
        "nullable_columns", "columns_with_defaults", "has_primary_key",
    }


# ---------------------------------------------------------------------------
# SchemaInspection
# ---------------------------------------------------------------------------

def test_inspect_empty_schema():
    si = inspect_schema(_schema())
    assert si.table_count == 0
    assert si.total_columns == 0
    assert si.total_indexes == 0


def test_inspect_schema_aggregates_columns():
    s = _schema(
        _table("a", cols=[_col("x"), _col("y")]),
        _table("b", cols=[_col("z")]),
    )
    si = inspect_schema(s)
    assert si.table_count == 2
    assert si.total_columns == 3


def test_inspect_schema_to_dict_has_tables_list():
    s = _schema(_table("t", cols=[_col("c")]))
    d = inspect_schema(s).to_dict()
    assert "tables" in d
    assert d["tables"][0]["name"] == "t"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, sql: str) -> Path:
    p = tmp_path / "schema.sql"
    p.write_text(sql)
    return p


def test_cli_missing_file_exits(tmp_path, capsys):
    from sqldiff.inspect_cli import main
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "missing.sql")])
    assert exc.value.code == 1


def test_cli_text_output(tmp_path, capsys):
    from sqldiff.inspect_cli import main
    p = _write(tmp_path, "CREATE TABLE users (id INTEGER NOT NULL, name TEXT);")
    main([str(p), "--format", "text"])
    out = capsys.readouterr().out
    assert "Tables" in out
    assert "users" in out


def test_cli_json_output(tmp_path, capsys):
    from sqldiff.inspect_cli import main
    p = _write(tmp_path, "CREATE TABLE orders (id INTEGER NOT NULL);")
    main([str(p), "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["table_count"] == 1


def test_cli_single_table_json(tmp_path, capsys):
    from sqldiff.inspect_cli import main
    p = _write(tmp_path, "CREATE TABLE items (id INTEGER NOT NULL, qty INTEGER);")
    main([str(p), "--format", "json", "--table", "items"])
    data = json.loads(capsys.readouterr().out)
    assert data["name"] == "items"
    assert data["column_count"] == 2


def test_cli_unknown_table_exits(tmp_path, capsys):
    from sqldiff.inspect_cli import main
    p = _write(tmp_path, "CREATE TABLE items (id INTEGER NOT NULL);")
    with pytest.raises(SystemExit) as exc:
        main([str(p), "--table", "nonexistent"])
    assert exc.value.code == 1
