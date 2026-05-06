"""Tests for sqldiff.migrator."""

import pytest

from sqldiff.schema import Column, Table, Schema
from sqldiff.differ import SchemaDiff, TableDiff
from sqldiff.migrator import generate_migration, MigrationScript


def _col(name: str, col_type: str = "TEXT", nullable: bool = True, default=None) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable, default=default)


def _table(name: str, cols=None) -> Table:
    return Table(name=name, columns=cols or [_col("id", "INTEGER")], indexes=[])


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(tables_added=[], tables_removed=[], tables_modified=[])


def test_empty_diff_produces_empty_script():
    script = generate_migration(_empty_diff())
    assert script.is_empty()
    assert script.up() == ""
    assert script.down() == ""


def test_table_added_generates_create_and_drop():
    table = _table("users", [_col("id", "INTEGER"), _col("email", "TEXT")])
    diff = SchemaDiff(tables_added=[table], tables_removed=[], tables_modified=[])
    script = generate_migration(diff)

    assert "CREATE TABLE users" in script.up()
    assert "id INTEGER" in script.up()
    assert "email TEXT" in script.up()
    assert "DROP TABLE IF EXISTS users" in script.down()


def test_table_removed_generates_drop_and_create():
    table = _table("orders", [_col("id", "INTEGER")])
    diff = SchemaDiff(tables_added=[], tables_removed=[table], tables_modified=[])
    script = generate_migration(diff)

    assert "DROP TABLE IF EXISTS orders" in script.up()
    assert "CREATE TABLE orders" in script.down()


def test_column_added_generates_alter_add():
    new_col = _col("age", "INTEGER", nullable=False)
    td = TableDiff(table_name="users", columns_added=[new_col], columns_removed=[], columns_modified=[])
    diff = SchemaDiff(tables_added=[], tables_removed=[], tables_modified=[td])
    script = generate_migration(diff)

    assert "ALTER TABLE users ADD COLUMN age INTEGER NOT NULL" in script.up()
    assert "ALTER TABLE users DROP COLUMN age" in script.down()


def test_column_removed_generates_alter_drop():
    old_col = _col("bio", "TEXT")
    td = TableDiff(table_name="users", columns_added=[], columns_removed=[old_col], columns_modified=[])
    diff = SchemaDiff(tables_added=[], tables_removed=[], tables_modified=[td])
    script = generate_migration(diff)

    assert "ALTER TABLE users DROP COLUMN bio" in script.up()
    assert "ALTER TABLE users ADD COLUMN bio TEXT" in script.down()


def test_column_with_default_includes_default():
    col = _col("status", "TEXT", nullable=True, default="'active'")
    td = TableDiff(table_name="posts", columns_added=[col], columns_removed=[], columns_modified=[])
    diff = SchemaDiff(tables_added=[], tables_removed=[], tables_modified=[td])
    script = generate_migration(diff)

    assert "DEFAULT 'active'" in script.up()


def test_migration_script_is_not_empty_when_has_statements():
    table = _table("logs")
    diff = SchemaDiff(tables_added=[table], tables_removed=[], tables_modified=[])
    script = generate_migration(diff)
    assert not script.is_empty()
