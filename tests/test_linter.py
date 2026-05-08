"""Tests for sqldiff.linter."""
import pytest

from sqldiff.schema import Column, Index, Schema, Table
from sqldiff.linter import LintIssue, LintResult, lint_schema


def _col(name: str, col_type: str = "TEXT", nullable: bool = True, default=None) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable, default=default)


def _table(name: str, columns: list) -> Table:
    return Table(name=name, columns=columns, indexes=[])


def _schema(*tables: Table) -> Schema:
    return Schema(tables={t.name: t for t in tables})


# ---------------------------------------------------------------------------
# LintIssue __str__
# ---------------------------------------------------------------------------

def test_lint_issue_str_with_column():
    issue = LintIssue(table="users", column="name col", code="L002",
                      message="spaces", severity="error")
    assert "users.name col" in str(issue)
    assert "L002" in str(issue)
    assert "ERROR" in str(issue)


def test_lint_issue_str_without_column():
    issue = LintIssue(table="orders", column=None, code="L001",
                      message="no pk", severity="warning")
    assert str(issue).startswith("[WARNING]")
    assert "orders" in str(issue)
    assert "orders." not in str(issue)


# ---------------------------------------------------------------------------
# LintResult helpers
# ---------------------------------------------------------------------------

def test_lint_result_is_clean_when_no_issues():
    assert LintResult().is_clean


def test_lint_result_errors_and_warnings_split():
    r = LintResult(issues=[
        LintIssue("t", None, "L001", "msg", "warning"),
        LintIssue("t", "c", "L002", "msg", "error"),
    ])
    assert len(r.errors) == 1
    assert len(r.warnings) == 1
    assert not r.is_clean


# ---------------------------------------------------------------------------
# L001 – no primary key
# ---------------------------------------------------------------------------

def test_no_pk_warning():
    table = _table("logs", [_col("created_at", "DATETIME")])
    result = lint_schema(_schema(table))
    codes = [i.code for i in result.issues]
    assert "L001" in codes


def test_pk_named_id_suppresses_l001():
    table = _table("users", [_col("id", "INTEGER", nullable=False)])
    result = lint_schema(_schema(table))
    codes = [i.code for i in result.issues]
    assert "L001" not in codes


# ---------------------------------------------------------------------------
# L002 – column name with spaces
# ---------------------------------------------------------------------------

def test_column_with_space_raises_error():
    table = _table("bad", [_col("first name", "VARCHAR"), _col("id", "INT")])
    result = lint_schema(_schema(table))
    errors = [i for i in result.issues if i.code == "L002"]
    assert len(errors) == 1
    assert errors[0].severity == "error"
    assert errors[0].column == "first name"


# ---------------------------------------------------------------------------
# L003 – TEXT/BLOB with default
# ---------------------------------------------------------------------------

def test_text_with_default_warns():
    table = _table("docs", [
        _col("id", "INTEGER", nullable=False),
        _col("body", "TEXT", nullable=True, default="''"),
    ])
    result = lint_schema(_schema(table))
    codes = [i.code for i in result.issues]
    assert "L003" in codes


def test_text_without_default_no_l003():
    table = _table("docs", [
        _col("id", "INTEGER", nullable=False),
        _col("body", "TEXT", nullable=True, default=None),
    ])
    result = lint_schema(_schema(table))
    codes = [i.code for i in result.issues]
    assert "L003" not in codes


# ---------------------------------------------------------------------------
# L004 – nullable FK-style column
# ---------------------------------------------------------------------------

def test_nullable_fk_column_warns():
    table = _table("orders", [
        _col("id", "INTEGER", nullable=False),
        _col("user_id", "INTEGER", nullable=True),
    ])
    result = lint_schema(_schema(table))
    codes = [i.code for i in result.issues]
    assert "L004" in codes


def test_not_null_fk_column_no_l004():
    table = _table("orders", [
        _col("id", "INTEGER", nullable=False),
        _col("user_id", "INTEGER", nullable=False),
    ])
    result = lint_schema(_schema(table))
    codes = [i.code for i in result.issues]
    assert "L004" not in codes


# ---------------------------------------------------------------------------
# Empty schema
# ---------------------------------------------------------------------------

def test_empty_schema_is_clean():
    result = lint_schema(Schema(tables={}))
    assert result.is_clean
