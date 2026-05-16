"""Tests for sqldiff.stat_cli."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from sqldiff.stat_cli import build_stat_parser, main


def _write(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(content)
    return str(p)


SIMPLE_SQL = "CREATE TABLE users (id INTEGER NOT NULL, name TEXT);\n"
EXTRA_SQL = "CREATE TABLE users (id INTEGER NOT NULL, name TEXT);\nCREATE TABLE orders (id INTEGER NOT NULL);\n"


# ── Parser defaults ───────────────────────────────────────────────────────────

def test_build_stat_parser_defaults():
    p = build_stat_parser()
    args = p.parse_args(["a.sql", "b.sql"])
    assert args.before == "a.sql"
    assert args.after == "b.sql"
    assert args.format == "text"
    assert args.exit_code is False


def test_build_stat_parser_json_flag():
    p = build_stat_parser()
    args = p.parse_args(["a.sql", "b.sql", "--format", "json"])
    assert args.format == "json"


def test_build_stat_parser_exit_code_flag():
    p = build_stat_parser()
    args = p.parse_args(["a.sql", "b.sql", "--exit-code"])
    assert args.exit_code is True


# ── main ──────────────────────────────────────────────────────────────────────

def test_main_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "missing.sql"), str(tmp_path / "also.sql")])
    assert exc.value.code == 2


def test_main_no_changes_text(tmp_path, capsys):
    f = _write(tmp_path, "schema.sql", SIMPLE_SQL)
    main([f, f])
    out = capsys.readouterr().out
    assert "0" in out


def test_main_with_changes_text(tmp_path, capsys):
    before = _write(tmp_path, "before.sql", SIMPLE_SQL)
    after = _write(tmp_path, "after.sql", EXTRA_SQL)
    main([before, after])
    out = capsys.readouterr().out
    assert "orders" in out or "1" in out


def test_main_json_output(tmp_path, capsys):
    before = _write(tmp_path, "before.sql", SIMPLE_SQL)
    after = _write(tmp_path, "after.sql", EXTRA_SQL)
    main([before, after, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "tables_added" in data
    assert "total_changes" in data


def test_main_exit_code_when_changes(tmp_path):
    before = _write(tmp_path, "before.sql", SIMPLE_SQL)
    after = _write(tmp_path, "after.sql", EXTRA_SQL)
    with pytest.raises(SystemExit) as exc:
        main([before, after, "--exit-code"])
    assert exc.value.code == 1


def test_main_no_exit_code_when_no_changes(tmp_path):
    f = _write(tmp_path, "schema.sql", SIMPLE_SQL)
    # Should not raise
    main([f, f, "--exit-code"])
