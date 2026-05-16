"""Tests for sqldiff.classifier."""
import pytest

from sqldiff.classifier import ClassificationReport, RiskLevel, RiskItem, classify_diff
from sqldiff.differ import SchemaDiff
from sqldiff.schema import Column, Index, Table
from sqldiff.comparator import TableDiff, ColumnDiff


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _col(name: str, col_type: str = "TEXT", not_null: bool = False, default=None) -> Column:
    return Column(name=name, col_type=col_type, not_null=not_null, default=default)


def _idx(name: str, columns=None) -> Index:
    return Index(name=name, columns=columns or ["id"], unique=False)


def _table(name: str, columns=None, indexes=None) -> Table:
    return Table(name=name, columns=columns or [], indexes=indexes or [])


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(tables_added=[], tables_removed=[], tables_modified={})


# ---------------------------------------------------------------------------
# RiskItem / ClassificationReport unit tests
# ---------------------------------------------------------------------------

def test_risk_item_str():
    item = RiskItem(table="users", description="Table removed", level=RiskLevel.HIGH)
    assert str(item) == "[HIGH] users: Table removed"


def test_report_is_empty_when_no_items():
    report = ClassificationReport()
    assert report.is_empty()


def test_report_by_level_filters_correctly():
    items = [
        RiskItem("a", "x", RiskLevel.LOW),
        RiskItem("b", "y", RiskLevel.HIGH),
        RiskItem("c", "z", RiskLevel.LOW),
    ]
    report = ClassificationReport(items=items)
    assert len(report.by_level(RiskLevel.LOW)) == 2
    assert len(report.by_level(RiskLevel.HIGH)) == 1
    assert len(report.by_level(RiskLevel.MEDIUM)) == 0


def test_report_highest_risk_all_low():
    report = ClassificationReport(items=[RiskItem("t", "d", RiskLevel.LOW)])
    assert report.highest_risk() == RiskLevel.LOW


def test_report_highest_risk_medium():
    report = ClassificationReport(items=[
        RiskItem("t", "d", RiskLevel.LOW),
        RiskItem("t", "d", RiskLevel.MEDIUM),
    ])
    assert report.highest_risk() == RiskLevel.MEDIUM


def test_report_highest_risk_high_wins():
    report = ClassificationReport(items=[
        RiskItem("t", "d", RiskLevel.MEDIUM),
        RiskItem("t", "d", RiskLevel.HIGH),
    ])
    assert report.highest_risk() == RiskLevel.HIGH


# ---------------------------------------------------------------------------
# classify_diff integration tests
# ---------------------------------------------------------------------------

def test_classify_empty_diff_produces_no_items():
    report = classify_diff(_empty_diff())
    assert report.is_empty()


def test_classify_table_added_is_low_risk():
    diff = SchemaDiff(tables_added=["orders"], tables_removed=[], tables_modified={})
    report = classify_diff(diff)
    assert len(report.items) == 1
    assert report.items[0].level == RiskLevel.LOW


def test_classify_table_removed_is_high_risk():
    diff = SchemaDiff(tables_added=[], tables_removed=["orders"], tables_modified={})
    report = classify_diff(diff)
    assert report.items[0].level == RiskLevel.HIGH


def test_classify_column_removed_is_high_risk():
    col = _col("email")
    td = TableDiff(
        columns_added=[],
        columns_removed=[col],
        columns_modified=[],
        indexes_added=[],
        indexes_removed=[],
    )
    diff = SchemaDiff(tables_added=[], tables_removed=[], tables_modified={"users": td})
    report = classify_diff(diff)
    high = report.by_level(RiskLevel.HIGH)
    assert any("email" in i.description for i in high)


def test_classify_not_null_column_added_without_default_is_medium():
    col = _col("verified", not_null=True, default=None)
    td = TableDiff(
        columns_added=[col],
        columns_removed=[],
        columns_modified=[],
        indexes_added=[],
        indexes_removed=[],
    )
    diff = SchemaDiff(tables_added=[], tables_removed=[], tables_modified={"users": td})
    report = classify_diff(diff)
    medium = report.by_level(RiskLevel.MEDIUM)
    assert any("verified" in i.description for i in medium)


def test_classify_nullable_column_added_is_low():
    col = _col("nickname", not_null=False)
    td = TableDiff(
        columns_added=[col],
        columns_removed=[],
        columns_modified=[],
        indexes_added=[],
        indexes_removed=[],
    )
    diff = SchemaDiff(tables_added=[], tables_removed=[], tables_modified={"users": td})
    report = classify_diff(diff)
    low = report.by_level(RiskLevel.LOW)
    assert any("nickname" in i.description for i in low)


def test_classify_type_change_is_high_risk():
    cd = ColumnDiff(name="age", type_changed=True, old_type="INT", new_type="TEXT",
                    nullability_changed=False, default_changed=False)
    td = TableDiff(
        columns_added=[],
        columns_removed=[],
        columns_modified=[cd],
        indexes_added=[],
        indexes_removed=[],
    )
    diff = SchemaDiff(tables_added=[], tables_removed=[], tables_modified={"users": td})
    report = classify_diff(diff)
    high = report.by_level(RiskLevel.HIGH)
    assert any("age" in i.description for i in high)
