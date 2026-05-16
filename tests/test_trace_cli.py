"""Tests for sqldiff.trace_cli."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqldiff.trace_cli import build_trace_parser, main


CREATE_V1 = "CREATE TABLE users (id INTEGER NOT NULL, name TEXT);"
CREATE_V2 = "CREATE TABLE users (id INTEGER NOT NULL, name TEXT, email TEXT);"


def _write(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(content)
    return str(p)


# ---------------------------------------------------------------------------
# build_trace_parser
# ---------------------------------------------------------------------------

def test_build_trace_parser_defaults():
    p = build_trace_parser()
    args = p.parse_args(["v1:a.sql", "v2:b.sql"])
    assert args.snapshots == ["v1:a.sql", "v2:b.sql"]
    assert args.format == "text"
    assert args.table is None
    assert args.column is None


def test_build_trace_parser_options():
    p = build_trace_parser()
    args = p.parse_args(["v1:a.sql", "--table", "users", "--column", "id", "--format", "json"])
    assert args.table == "users"
    assert args.column == "id"
    assert args.format == "json"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def test_main_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit):
        main(["v1:/nonexistent/path/schema.sql"])


def test_main_column_without_table_exits(tmp_path):
    f = _write(tmp_path, "v1.sql", CREATE_V1)
    with pytest.raises(SystemExit):
        main([f"v1:{f}", "--column", "id"])


def test_main_text_output(tmp_path, capsys):
    f1 = _write(tmp_path, "v1.sql", CREATE_V1)
    f2 = _write(tmp_path, "v2.sql", CREATE_V2)
    main([f"v1:{f1}", f"v2:{f2}"])
    out = capsys.readouterr().out
    assert "users" in out


def test_main_json_output(tmp_path, capsys):
    f1 = _write(tmp_path, "v1.sql", CREATE_V1)
    f2 = _write(tmp_path, "v2.sql", CREATE_V2)
    main([f"v1:{f1}", f"v2:{f2}", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert all("table" in item and "column" in item for item in data)


def test_main_filter_table(tmp_path, capsys):
    extra = "CREATE TABLE orders (oid INTEGER);" + CREATE_V1
    f1 = _write(tmp_path, "v1.sql", extra)
    f2 = _write(tmp_path, "v2.sql", CREATE_V2 + "CREATE TABLE orders (oid INTEGER);")
    main([f"v1:{f1}", f"v2:{f2}", "--table", "users"])
    out = capsys.readouterr().out
    assert "users" in out
    assert "orders" not in out


def test_main_filter_column(tmp_path, capsys):
    f1 = _write(tmp_path, "v1.sql", CREATE_V1)
    f2 = _write(tmp_path, "v2.sql", CREATE_V2)
    main([f"v1:{f1}", f"v2:{f2}", "--table", "users", "--column", "id"])
    out = capsys.readouterr().out
    assert "id" in out
