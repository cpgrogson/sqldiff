"""Tests for sqldiff.watcher."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sqldiff.schema import Schema, Table, Column
from sqldiff.differ import SchemaDiff
from sqldiff.watcher import SchemaWatcher, _file_checksum, _build_state


SQL_V1 = textwrap.dedent("""\
    CREATE TABLE users (
        id INTEGER NOT NULL,
        name TEXT
    );
""")

SQL_V2 = textwrap.dedent("""\
    CREATE TABLE users (
        id INTEGER NOT NULL,
        name TEXT,
        email TEXT
    );
""")


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def test_file_checksum_changes_with_content(tmp_path):
    f = tmp_path / "schema.sql"
    _write(f, SQL_V1)
    c1 = _file_checksum(f)
    _write(f, SQL_V2)
    c2 = _file_checksum(f)
    assert c1 != c2


def test_file_checksum_stable(tmp_path):
    f = tmp_path / "schema.sql"
    _write(f, SQL_V1)
    assert _file_checksum(f) == _file_checksum(f)


def test_build_state_returns_watch_state(tmp_path):
    f = tmp_path / "schema.sql"
    _write(f, SQL_V1)
    state = _build_state(f)
    assert state.path == f
    assert isinstance(state.schema, Schema)
    assert len(state.checksum) == 32  # MD5 hex


def test_run_once_initialises_without_callback(tmp_path):
    f = tmp_path / "schema.sql"
    _write(f, SQL_V1)
    callback = MagicMock()
    watcher = SchemaWatcher([f], on_change=callback)
    watcher.run_once()  # initialise pass — no callback expected
    callback.assert_not_called()


def test_run_once_detects_change(tmp_path):
    f = tmp_path / "schema.sql"
    _write(f, SQL_V1)
    callback = MagicMock()
    watcher = SchemaWatcher([f], on_change=callback)
    watcher.run_once()  # initialise
    _write(f, SQL_V2)   # mutate file
    watcher.run_once()  # detect change
    callback.assert_called_once()
    path_arg, diff_arg = callback.call_args[0]
    assert path_arg == f
    assert isinstance(diff_arg, SchemaDiff)


def test_run_once_no_spurious_callback(tmp_path):
    f = tmp_path / "schema.sql"
    _write(f, SQL_V1)
    callback = MagicMock()
    watcher = SchemaWatcher([f], on_change=callback)
    watcher.run_once()  # initialise
    watcher.run_once()  # no file change
    callback.assert_not_called()


def test_watch_respects_max_iterations(tmp_path):
    f = tmp_path / "schema.sql"
    _write(f, SQL_V1)
    callback = MagicMock()
    watcher = SchemaWatcher([f], on_change=callback, interval=0.0)
    watcher.watch(max_iterations=3)
    # No changes written, callback should never fire
    callback.assert_not_called()
