"""Tests for sqldiff.cli module."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from sqldiff.cli import main, build_parser
from sqldiff.differ import SchemaDiff


OLD_SQL = "CREATE TABLE users (id INTEGER NOT NULL, name TEXT);"
NEW_SQL = "CREATE TABLE users (id INTEGER NOT NULL, name TEXT, email TEXT);"


def _write(tmp_path, filename, content):
    p = tmp_path / filename
    p.write_text(content)
    return str(p)


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["old.sql", "new.sql"])
    assert args.old == "old.sql"
    assert args.new == "new.sql"
    assert args.output_format == "text"
    assert args.exit_code is False


def test_main_no_changes(tmp_path):
    old = _write(tmp_path, "old.sql", OLD_SQL)
    new = _write(tmp_path, "new.sql", OLD_SQL)
    result = main([old, new])
    assert result == 0


def test_main_with_changes_exit_code(tmp_path):
    old = _write(tmp_path, "old.sql", OLD_SQL)
    new = _write(tmp_path, "new.sql", NEW_SQL)
    result = main([old, new, "--exit-code"])
    assert result == 1


def test_main_json_format(tmp_path, capsys):
    old = _write(tmp_path, "old.sql", OLD_SQL)
    new = _write(tmp_path, "new.sql", NEW_SQL)
    main([old, new, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "modified_tables" in data


def test_main_with_title(tmp_path, capsys):
    old = _write(tmp_path, "old.sql", OLD_SQL)
    new = _write(tmp_path, "new.sql", OLD_SQL)
    main([old, new, "--title", "Release 2.0"])
    captured = capsys.readouterr()
    assert "Release 2.0" in captured.out


def test_main_file_not_found(tmp_path):
    result = main(["nonexistent_old.sql", "nonexistent_new.sql"])
    assert result == 2


def test_main_no_exit_code_even_with_changes(tmp_path):
    old = _write(tmp_path, "old.sql", OLD_SQL)
    new = _write(tmp_path, "new.sql", NEW_SQL)
    result = main([old, new])
    assert result == 0
