"""Tests for sqldiff.tag_cli."""
import json
import os
from pathlib import Path

import pytest

from sqldiff.tag_cli import build_tag_parser, _STORE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SIMPLE_SQL = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL);"
ALTERED_SQL = (
    "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT);"
)


def _write(tmp_path: Path, filename: str, content: str) -> str:
    p = tmp_path / filename
    p.write_text(content)
    return str(p)


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_build_tag_parser_defaults():
    parser = build_tag_parser()
    args = parser.parse_args(['tag', 'old.sql', 'new.sql'])
    assert args.old == 'old.sql'
    assert args.new == 'new.sql'
    assert args.tags == []
    assert args.format == 'text'


def test_build_tag_parser_with_tags():
    parser = build_tag_parser()
    args = parser.parse_args(['tag', 'a.sql', 'b.sql', '--tags', 'v1', 'hotfix'])
    assert args.tags == ['v1', 'hotfix']


def test_build_tag_parser_list_command():
    parser = build_tag_parser()
    args = parser.parse_args(['list'])
    assert args.command == 'list'
    assert args.format == 'text'


def test_build_tag_parser_list_json():
    parser = build_tag_parser()
    args = parser.parse_args(['list', '--format', 'json'])
    assert args.format == 'json'


# ---------------------------------------------------------------------------
# Integration – tag command (text)
# ---------------------------------------------------------------------------

def test_tag_no_changes_returns_zero(tmp_path, capsys):
    from sqldiff.tag_cli import main
    old = _write(tmp_path, 'old.sql', SIMPLE_SQL)
    new = _write(tmp_path, 'new.sql', SIMPLE_SQL)
    rc = main(['tag', old, new, '--tags', 'stable'])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'stable' in out


def test_tag_with_changes_returns_one(tmp_path, capsys):
    from sqldiff.tag_cli import main
    old = _write(tmp_path, 'old.sql', SIMPLE_SQL)
    new = _write(tmp_path, 'new.sql', ALTERED_SQL)
    rc = main(['tag', old, new, '--tags', 'migration'])
    assert rc == 1
    out = capsys.readouterr().out
    assert 'migration' in out


def test_tag_json_format(tmp_path, capsys):
    from sqldiff.tag_cli import main
    old = _write(tmp_path, 'old.sql', SIMPLE_SQL)
    new = _write(tmp_path, 'new.sql', ALTERED_SQL)
    main(['tag', old, new, '--tags', 'v2', '--format', 'json'])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert 'v2' in payload['tags']
    assert payload['has_changes'] is True


def test_tag_missing_file_exits(tmp_path, capsys):
    from sqldiff.tag_cli import main
    rc = main(['tag', 'nonexistent_old.sql', 'nonexistent_new.sql'])
    assert rc == 2
    err = capsys.readouterr().err
    assert 'error' in err
