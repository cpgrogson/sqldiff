"""Tests for sqldiff.renamer."""
import pytest

from sqldiff.schema import Schema, Table, Column, Index
from sqldiff.differ import SchemaDiff
from sqldiff.renamer import RenameCandidate, RenameReport, detect_renames, _column_similarity


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _col(name: str, col_type: str = "TEXT", nullable: bool = True, default=None) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable, default=default)


def _table(name: str, cols=None) -> Table:
    return Table(name=name, columns=cols or [_col("id", "INTEGER")], indexes=[])


def _schema(*tables: Table) -> Schema:
    return Schema(tables={t.name: t for t in tables})


def _diff(
    old: Schema,
    new: Schema,
    added=(),
    removed=(),
    modified=(),
) -> SchemaDiff:
    return SchemaDiff(
        tables_added=list(added),
        tables_removed=list(removed),
        tables_modified=list(modified),
    )


# ---------------------------------------------------------------------------
# RenameCandidate.__str__
# ---------------------------------------------------------------------------

def test_rename_candidate_str_table():
    c = RenameCandidate(old_name="users", new_name="accounts", score=0.75, kind="table")
    s = str(c)
    assert "users" in s
    assert "accounts" in s
    assert "0.75" in s


def test_rename_candidate_str_column():
    c = RenameCandidate(
        old_name="usr_id", new_name="user_id", score=0.82, kind="column", table="orders"
    )
    s = str(c)
    assert "orders" in s
    assert "usr_id" in s
    assert "user_id" in s


# ---------------------------------------------------------------------------
# RenameReport helpers
# ---------------------------------------------------------------------------

def test_rename_report_is_empty():
    assert RenameReport().is_empty()


def test_rename_report_tables_and_columns():
    r = RenameReport(
        candidates=[
            RenameCandidate("a", "b", 0.9, "table"),
            RenameCandidate("x", "y", 0.8, "column", table="t"),
        ]
    )
    assert len(r.tables()) == 1
    assert len(r.columns()) == 1


# ---------------------------------------------------------------------------
# _column_similarity
# ---------------------------------------------------------------------------

def test_column_similarity_identical():
    c = _col("email", "TEXT", False, "''")
    assert _column_similarity(c, c) >= 0.9


def test_column_similarity_different_type():
    a = _col("val", "INTEGER")
    b = _col("val", "TEXT")
    # type mismatch should lower the score
    assert _column_similarity(a, b) < _column_similarity(a, a)


# ---------------------------------------------------------------------------
# detect_renames — table level
# ---------------------------------------------------------------------------

def test_detect_table_rename():
    old = _schema(_table("user_accounts"))
    new = _schema(_table("user_account"))
    d = _diff(old, new, added=["user_account"], removed=["user_accounts"])
    report = detect_renames(d, old, new, threshold=0.5)
    assert not report.is_empty()
    assert report.tables()[0].old_name == "user_accounts"
    assert report.tables()[0].new_name == "user_account"


def test_detect_no_table_rename_below_threshold():
    old = _schema(_table("orders"))
    new = _schema(_table("invoices"))
    d = _diff(old, new, added=["invoices"], removed=["orders"])
    report = detect_renames(d, old, new, threshold=0.9)
    assert report.is_empty()


# ---------------------------------------------------------------------------
# detect_renames — column level
# ---------------------------------------------------------------------------

def test_detect_column_rename():
    cols_old = [_col("id", "INTEGER"), _col("usr_name", "TEXT", False)]
    cols_new = [_col("id", "INTEGER"), _col("user_name", "TEXT", False)]
    old = _schema(Table(name="accounts", columns=cols_old, indexes=[]))
    new = _schema(Table(name="accounts", columns=cols_new, indexes=[]))
    d = _diff(old, new)  # no added/removed tables
    report = detect_renames(d, old, new, threshold=0.4)
    col_renames = report.columns()
    assert any(c.old_name == "usr_name" and c.new_name == "user_name" for c in col_renames)


def test_detect_no_column_rename_completely_different():
    cols_old = [_col("alpha", "INTEGER")]
    cols_new = [_col("zzzzzz", "TEXT")]
    old = _schema(Table(name="t", columns=cols_old, indexes=[]))
    new = _schema(Table(name="t", columns=cols_new, indexes=[]))
    d = _diff(old, new)
    report = detect_renames(d, old, new, threshold=0.8)
    assert report.columns() == []


def test_candidates_sorted_by_score_descending():
    cols_old = [_col("id", "INTEGER"), _col("usr_nm", "TEXT"), _col("addr", "TEXT")]
    cols_new = [_col("id", "INTEGER"), _col("user_name", "TEXT"), _col("address", "TEXT")]
    old = _schema(Table(name="t", columns=cols_old, indexes=[]))
    new = _schema(Table(name="t", columns=cols_new, indexes=[]))
    d = _diff(old, new)
    report = detect_renames(d, old, new, threshold=0.3)
    scores = [c.score for c in report.candidates]
    assert scores == sorted(scores, reverse=True)
