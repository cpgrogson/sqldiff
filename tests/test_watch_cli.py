"""Tests for sqldiff.watch_cli."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sqldiff.watch_cli import build_watch_parser, main, _make_callback
from sqldiff.differ import SchemaDiff


SQL = textwrap.dedent("""\
    CREATE TABLE orders (
        id INTEGER NOT NULL
    );
""")


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def test_build_watch_parser_defaults():
    parser = build_watch_parser()
    args = parser.parse_args(["a.sql"])
    assert args.files == ["a.sql"]
    assert args.interval == 2.0
    assert args.fmt == "text"
    assert args.quiet is False


def test_build_watch_parser_options():
    parser = build_watch_parser()
    args = parser.parse_args(["a.sql", "--interval", "5", "--format", "json", "--quiet"])
    assert args.interval == 5.0
    assert args.fmt == "json"
    assert args.quiet is True


def test_main_missing_file_exits(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent.sql"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_calls_watcher(tmp_path):
    f = tmp_path / "schema.sql"
    _write(f, SQL)
    with patch("sqldiff.watch_cli.SchemaWatcher") as MockWatcher:
        instance = MockWatcher.return_value
        main([str(f), "--interval", "0"])
        MockWatcher.assert_called_once()
        instance.watch.assert_called_once()


def test_callback_text_format(capsys, tmp_path):
    f = tmp_path / "schema.sql"
    diff = MagicMock(spec=SchemaDiff)
    diff.has_changes = True
    diff.added_tables = ["orders"]
    diff.removed_tables = []
    diff.modified_tables = {}
    callback = _make_callback(fmt="text", quiet=False)
    with patch("sqldiff.watch_cli.format_text", return_value="--- diff ---") as mock_fmt:
        callback(f, diff)
        mock_fmt.assert_called_once_with(diff)
    captured = capsys.readouterr()
    assert "--- diff ---" in captured.out


def test_callback_quiet_suppresses_no_change(capsys, tmp_path):
    f = tmp_path / "schema.sql"
    diff = MagicMock(spec=SchemaDiff)
    diff.has_changes = False
    callback = _make_callback(fmt="text", quiet=True)
    with patch("sqldiff.watch_cli.format_text") as mock_fmt:
        callback(f, diff)
        mock_fmt.assert_not_called()
    captured = capsys.readouterr()
    assert captured.out == ""


def test_callback_json_format(capsys, tmp_path):
    f = tmp_path / "schema.sql"
    diff = MagicMock(spec=SchemaDiff)
    diff.has_changes = True
    callback = _make_callback(fmt="json", quiet=False)
    payload = json.dumps({"added": []})
    with patch("sqldiff.watch_cli.format_json", return_value=payload):
        callback(f, diff)
    captured = capsys.readouterr()
    assert payload in captured.out
