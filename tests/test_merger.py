import pytest
from sqldiff.schema import Schema, Table, Column, Index
from sqldiff.merger import merge_schemas, MergeConflict


def _col(name: str, col_type: str = "TEXT", nullable: bool = True, default=None) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable, default=default)


def _idx(name: str, columns=None, unique: bool = False) -> Index:
    return Index(name=name, columns=columns or [], unique=unique)


def _table(name: str, columns=None, indexes=None) -> Table:
    return Table(name=name, columns=columns or [], indexes=indexes or [])


def _schema(*tables: Table) -> Schema:
    return Schema(tables=list(tables))


# --- no conflict cases ---

def test_merge_identical_schemas_no_conflicts():
    s = _schema(_table("users", [_col("id", "INT")]))
    result = merge_schemas(s, s)
    assert not result.has_conflicts
    assert len(result.schema.tables) == 1


def test_merge_adds_table_from_other():
    base = _schema(_table("users", [_col("id", "INT")]))
    other = _schema(
        _table("users", [_col("id", "INT")]),
        _table("orders", [_col("order_id", "INT")]),
    )
    result = merge_schemas(base, other)
    names = {t.name for t in result.schema.tables}
    assert "orders" in names
    assert not result.has_conflicts


def test_merge_keeps_table_only_in_base():
    base = _schema(_table("users"), _table("logs"))
    other = _schema(_table("users"))
    result = merge_schemas(base, other)
    names = {t.name for t in result.schema.tables}
    assert "logs" in names


def test_merge_adds_column_from_other():
    base = _schema(_table("users", [_col("id", "INT")]))
    other = _schema(_table("users", [_col("id", "INT"), _col("email", "TEXT")]))
    result = merge_schemas(base, other)
    users = next(t for t in result.schema.tables if t.name == "users")
    col_names = [c.name for c in users.columns]
    assert "email" in col_names
    assert not result.has_conflicts


def test_merge_indexes_other_wins():
    base_idx = _idx("idx_email", ["email"], unique=False)
    other_idx = _idx("idx_email", ["email"], unique=True)
    base = _schema(_table("users", [_col("email")], [base_idx]))
    other = _schema(_table("users", [_col("email")], [other_idx]))
    result = merge_schemas(base, other)
    users = next(t for t in result.schema.tables if t.name == "users")
    assert users.indexes[0].unique is True


# --- conflict cases ---

def test_merge_column_type_conflict_recorded():
    base = _schema(_table("users", [_col("id", "INT")]))
    other = _schema(_table("users", [_col("id", "BIGINT")]))
    result = merge_schemas(base, other)
    assert result.has_conflicts
    assert len(result.conflicts) == 1
    c = result.conflicts[0]
    assert c.table_name == "users"
    assert c.column_name == "id"
    assert c.base_value == "INT"
    assert c.other_value == "BIGINT"


def test_merge_conflict_other_value_wins():
    base = _schema(_table("users", [_col("id", "INT")]))
    other = _schema(_table("users", [_col("id", "BIGINT")]))
    result = merge_schemas(base, other)
    users = next(t for t in result.schema.tables if t.name == "users")
    assert users.columns[0].col_type == "BIGINT"


def test_merge_conflict_str():
    conflict = MergeConflict("users", "id", "INT", "BIGINT")
    s = str(conflict)
    assert "users" in s
    assert "id" in s
    assert "INT" in s
    assert "BIGINT" in s
