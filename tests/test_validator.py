"""Tests for sqldiff.validator."""

import pytest

from sqldiff.schema import Column, Index, Schema, Table
from sqldiff.validator import ValidationIssue, validate_schema


def _make_column(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def _make_index(name: str, columns: list) -> Index:
    return Index(name=name, columns=columns, unique=False)


def _make_table(name: str, columns=None, indexes=None) -> Table:
    return Table(
        name=name,
        columns=columns or [_make_column("id", "INTEGER")],
        indexes=indexes or [],
    )


def _make_schema(*tables: Table) -> Schema:
    return Schema(tables={t.name: t for t in tables})


def test_valid_schema_returns_no_issues():
    schema = _make_schema(
        _make_table("users", columns=[_make_column("id"), _make_column("email")]),
    )
    result = validate_schema(schema)
    assert len(result) == 0
    assert result.is_valid


def test_empty_schema_returns_no_issues():
    result = validate_schema(Schema(tables={}))
    assert result.is_valid
    assert len(result) == 0


def test_table_with_no_columns_is_error():
    table = Table(name="empty_table", columns=[], indexes=[])
    schema = _make_schema(table)
    result = validate_schema(schema)
    assert not result.is_valid
    assert len(result.errors) == 1
    assert "no columns" in result.errors[0].message.lower()


def test_duplicate_column_names_are_errors():
    cols = [_make_column("id"), _make_column("id")]
    table = Table(name="dupes", columns=cols, indexes=[])
    schema = _make_schema(table)
    result = validate_schema(schema)
    errors = [i for i in result.errors if "duplicate column" in i.message.lower()]
    assert len(errors) == 1
    assert "id" in errors[0].message


def test_duplicate_index_names_are_warnings():
    cols = [_make_column("id"), _make_column("name")]
    indexes = [
        _make_index("idx_name", ["name"]),
        _make_index("idx_name", ["name"]),
    ]
    table = Table(name="t", columns=cols, indexes=indexes)
    schema = _make_schema(table)
    result = validate_schema(schema)
    warnings = [i for i in result.warnings if "duplicate index" in i.message.lower()]
    assert len(warnings) == 1


def test_index_references_unknown_column_is_error():
    cols = [_make_column("id")]
    indexes = [_make_index("idx_missing", ["nonexistent"])]
    table = Table(name="t", columns=cols, indexes=indexes)
    schema = _make_schema(table)
    result = validate_schema(schema)
    errors = [i for i in result.errors if "unknown column" in i.message.lower()]
    assert len(errors) == 1
    assert "nonexistent" in errors[0].message


def test_validation_issue_str_format():
    issue = ValidationIssue(table="users", message="Something wrong.", severity="error")
    assert "[ERROR]" in str(issue)
    assert "users" in str(issue)
    assert "Something wrong." in str(issue)


def test_is_valid_true_when_only_warnings():
    cols = [_make_column("id"), _make_column("name")]
    indexes = [_make_index("idx", ["name"]), _make_index("idx", ["name"])]
    table = Table(name="t", columns=cols, indexes=indexes)
    schema = _make_schema(table)
    result = validate_schema(schema)
    assert result.is_valid  # warnings don't make it invalid
    assert len(result.warnings) >= 1
