"""Tests for sqldiff.plan_cli."""
from __future__ import annotations

import json
import os
import textwrap

import pytest

from sqldiff.plan_cli import build_plan_parser, main


DDL_OLD = textwrap.dedent("""
    CREATE TABLE users (
        id INTEGER NOT NULL,
        name TEXT
    );
""")

DDL_NEW = textwrap.dedent("""
    CREATE TABLE users (
        id INTEGER NOT NULL,
        name TEXT,
        email TEXT
    );
    CREATE TABLE orders (
        id INTEGER NOT NULL
    );
""")


def _write(tmp_path, filename: str, content: str) -> str:
    p = tmp_path / filename
    p.write_text(content)
    return str(p)


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_build_plan_parser_defaults():
    p = build_plan_parser()
    args = p.parse_args(["old.sql", "new.sql"])
    assert args.old == "old.sql"
    assert args.new == "new.sql"
    assert args.format == "text"
    assert args.exit_code is False


def test_build_plan_parser_json_format():
    p = build_plan_parser()
    args = p.parse_args(["a.sql", "b.sql", "--format", "json"])
    assert args.format == "json"


def test_build_plan_parser_exit_code_flag():
    p = build_plan_parser()
    args = p.parse_args(["a.sql", "b.sql", "--exit-code"])
    assert args.exit_code is True


# ---------------------------------------------------------------------------
# main() integration tests
# ---------------------------------------------------------------------------

def test_main_no_changes_text(tmp_path, capsys):
    old = _write(tmp_path, "old.sql", DDL_OLD)
    main([old, old])
    out = capsys.readouterr().out
    assert "No migration steps" in out


def test_main_with_changes_text(tmp_path, capsys):
    old = _write(tmp_path, "old.sql", DDL_OLD)
    new = _write(tmp_path, "new.sql", DDL_NEW)
    main([old, new])
    out = capsys.readouterr().out
    assert "create_table" in out or "alter_table" in out


def test_main_json_output(tmp_path, capsys):
    old = _write(tmp_path, "old.sql", DDL_OLD)
    new = _write(tmp_path, "new.sql", DDL_NEW)
    main([old, new, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "steps" in data
    assert "warnings" in data
    assert isinstance(data["steps"], list)


def test_main_exit_code_no_changes(tmp_path):
    old = _write(tmp_path, "old.sql", DDL_OLD)
    # Same file → no diff → should NOT raise SystemExit(1)
    main([old, old, "--exit-code"])


def test_main_exit_code_with_changes(tmp_path):
    old = _write(tmp_path, "old.sql", DDL_OLD)
    new = _write(tmp_path, "new.sql", DDL_NEW)
    with pytest.raises(SystemExit) as exc_info:
        main([old, new, "--exit-code"])
    assert exc_info.value.code == 1


def test_main_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent_old.sql", "nonexistent_new.sql"])
    assert exc_info.value.code == 2
