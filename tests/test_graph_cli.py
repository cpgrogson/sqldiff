"""Tests for sqldiff.graph_cli."""
import os
import textwrap

import pytest

from sqldiff.graph_cli import build_graph_parser, main


def _write(tmp_path, filename, content):
    p = tmp_path / filename
    p.write_text(textwrap.dedent(content))
    return str(p)


SIMPLE_SQL = """\
    CREATE TABLE users (id INTEGER, email TEXT);
    CREATE TABLE orders (id INTEGER, users_id INTEGER);
"""


def test_build_graph_parser_defaults():
    p = build_graph_parser()
    args = p.parse_args(["schema.sql"])
    assert args.source == "schema.sql"
    assert args.order is False
    assert args.roots is False
    assert args.leaves is False


def test_build_graph_parser_flags():
    p = build_graph_parser()
    args = p.parse_args(["schema.sql", "--order", "--roots"])
    assert args.order is True
    assert args.roots is True


def test_main_missing_file_exits(tmp_path):
    rc = main([str(tmp_path / "missing.sql")])
    assert rc == 1


def test_main_lists_all_tables(tmp_path, capsys):
    f = _write(tmp_path, "schema.sql", SIMPLE_SQL)
    rc = main([f])
    assert rc == 0
    out = capsys.readouterr().out
    assert "users" in out
    assert "orders" in out


def test_main_order_flag(tmp_path, capsys):
    f = _write(tmp_path, "schema.sql", SIMPLE_SQL)
    rc = main([f, "--order"])
    assert rc == 0
    out = capsys.readouterr().out
    lines = [l.split()[0] for l in out.strip().splitlines()]
    assert lines.index("users") < lines.index("orders")


def test_main_roots_flag(tmp_path, capsys):
    f = _write(tmp_path, "schema.sql", SIMPLE_SQL)
    rc = main([f, "--roots"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "users" in out


def test_main_leaves_flag(tmp_path, capsys):
    f = _write(tmp_path, "schema.sql", SIMPLE_SQL)
    rc = main([f, "--leaves"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "orders" in out
