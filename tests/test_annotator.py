"""Tests for sqldiff.annotator."""
import pytest

from sqldiff.annotator import annotate_diff, Annotation, AnnotatedDiff
from sqldiff.schema import Column, Index, Table, Schema
from sqldiff.differ import SchemaDiff
from sqldiff.comparator import TableDiff, ColumnDiff


def _col(name, col_type="TEXT", default=None, not_null=False):
    return Column(name=name, col_type=col_type, default=default, not_null=not_null)


def _table(name, cols=None, indexes=None):
    return Table(name=name, columns=cols or [], indexes=indexes or [])


def _empty_diff():
    return SchemaDiff(tables_added=[], tables_removed=[], tables_modified=[])


def test_empty_diff_produces_no_annotations():
    result = annotate_diff(_empty_diff())
    assert result.is_empty()
    assert result.annotations == []


def test_table_added_annotation():
    table = _table("users", cols=[_col("id", "INTEGER"), _col("email")])
    diff = SchemaDiff(tables_added=[table], tables_removed=[], tables_modified=[])
    result = annotate_diff(diff)
    assert not result.is_empty()
    anns = result.by_table("users")
    assert len(anns) == 1
    assert anns[0].kind == "table"
    assert anns[0].change == "added"
    assert "id" in anns[0].detail
    assert "email" in anns[0].detail


def test_table_removed_annotation():
    table = _table("orders")
    diff = SchemaDiff(tables_added=[], tables_removed=[table], tables_modified=[])
    result = annotate_diff(diff)
    anns = result.by_table("orders")
    assert len(anns) == 1
    assert anns[0].change == "removed"
    assert anns[0].detail == ""


def test_column_added_annotation():
    td = TableDiff(
        name="products",
        columns_added=[_col("price", "NUMERIC", default="0", not_null=True)],
        columns_removed=[],
        columns_modified=[],
        indexes_added=[],
        indexes_removed=[],
    )
    diff = SchemaDiff(tables_added=[], tables_removed=[], tables_modified=[td])
    result = annotate_diff(diff)
    anns = result.by_table("products")
    assert len(anns) == 1
    assert "price" in anns[0].change
    assert "NUMERIC" in anns[0].detail
    assert "NOT NULL" in anns[0].detail


def test_column_removed_annotation():
    td = TableDiff(
        name="products",
        columns_added=[],
        columns_removed=[_col("legacy")],
        columns_modified=[],
        indexes_added=[],
        indexes_removed=[],
    )
    diff = SchemaDiff(tables_added=[], tables_removed=[], tables_modified=[td])
    result = annotate_diff(diff)
    anns = result.by_table("products")
    assert anns[0].change == "'legacy' removed"


def test_column_modified_annotation():
    cd = ColumnDiff(
        name="status",
        old_type="TEXT", new_type="VARCHAR(32)",
        old_default=None, new_default="'active'",
        old_not_null=False, new_not_null=True,
    )
    td = TableDiff(
        name="users",
        columns_added=[], columns_removed=[],
        columns_modified=[cd],
        indexes_added=[], indexes_removed=[],
    )
    diff = SchemaDiff(tables_added=[], tables_removed=[], tables_modified=[td])
    result = annotate_diff(diff)
    anns = result.by_kind("column")
    assert len(anns) == 1
    assert "TEXT" in anns[0].detail
    assert "VARCHAR(32)" in anns[0].detail


def test_by_kind_filters_correctly():
    table = _table("t1", cols=[_col("id")])
    diff = SchemaDiff(tables_added=[table], tables_removed=[], tables_modified=[])
    result = annotate_diff(diff)
    assert len(result.by_kind("table")) == 1
    assert len(result.by_kind("column")) == 0


def test_annotation_str_without_detail():
    a = Annotation(table="t", kind="table", change="removed")
    assert str(a) == "[TABLE] t: removed"


def test_annotation_str_with_detail():
    a = Annotation(table="t", kind="column", change="'x' added", detail="TEXT")
    assert "→ TEXT" in str(a)
