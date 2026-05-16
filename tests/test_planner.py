"""Tests for sqldiff.planner."""
from __future__ import annotations

import pytest

from sqldiff.schema import Column, Table, Schema
from sqldiff.differ import SchemaDiff
from sqldiff.planner import MigrationPlan, PlanStep, plan_migration


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _col(name: str, typ: str = "TEXT") -> Column:
    return Column(name=name, col_type=typ, nullable=True, default=None)


def _table(name: str, cols: list | None = None) -> Table:
    return Table(name=name, columns=cols or [_col("id", "INTEGER")], indexes=[])


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(
        added_tables={},
        removed_tables={},
        modified_tables={},
    )


# ---------------------------------------------------------------------------
# PlanStep / MigrationPlan unit tests
# ---------------------------------------------------------------------------

def test_plan_step_str_with_detail():
    s = PlanStep(order=1, action="create_table", table="users", detail="some info")
    assert str(s) == "[01] create_table users — some info"


def test_plan_step_str_without_detail():
    s = PlanStep(order=3, action="drop_table", table="legacy")
    assert str(s) == "[03] drop_table legacy"


def test_migration_plan_is_empty_when_no_steps():
    plan = MigrationPlan()
    assert plan.is_empty()


def test_migration_plan_str_empty():
    plan = MigrationPlan()
    assert str(plan) == "No migration steps."


def test_migration_plan_str_with_steps():
    plan = MigrationPlan(steps=[PlanStep(1, "create_table", "users")])
    assert "create_table users" in str(plan)


def test_migration_plan_str_includes_warnings():
    plan = MigrationPlan(
        steps=[PlanStep(1, "create_table", "t")],
        warnings=["Something odd happened."],
    )
    assert "WARNING: Something odd happened." in str(plan)


# ---------------------------------------------------------------------------
# plan_migration integration tests
# ---------------------------------------------------------------------------

def test_empty_diff_produces_empty_plan():
    plan = plan_migration(_empty_diff())
    assert plan.is_empty()


def test_added_table_generates_create_step():
    diff = SchemaDiff(
        added_tables={"orders": _table("orders")},
        removed_tables={},
        modified_tables={},
    )
    plan = plan_migration(diff)
    assert len(plan.steps) == 1
    assert plan.steps[0].action == "create_table"
    assert plan.steps[0].table == "orders"


def test_removed_table_generates_drop_step():
    diff = SchemaDiff(
        added_tables={},
        removed_tables={"legacy": _table("legacy")},
        modified_tables={},
    )
    plan = plan_migration(diff)
    assert len(plan.steps) == 1
    assert plan.steps[0].action == "drop_table"
    assert plan.steps[0].table == "legacy"


def test_modified_table_generates_alter_step():
    from sqldiff.comparator import TableDiff
    tbl_diff = TableDiff(
        table_name="users",
        added_columns=[_col("email")],
        removed_columns=[],
        modified_columns=[],
        added_indexes=[],
        removed_indexes=[],
    )
    diff = SchemaDiff(
        added_tables={},
        removed_tables={},
        modified_tables={"users": tbl_diff},
    )
    plan = plan_migration(diff)
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.action == "alter_table"
    assert step.table == "users"
    assert "+1" in step.detail


def test_ordering_create_before_drop():
    from sqldiff.comparator import TableDiff
    tbl_diff = TableDiff(
        table_name="mid",
        added_columns=[],
        removed_columns=[_col("old")],
        modified_columns=[],
        added_indexes=[],
        removed_indexes=[],
    )
    diff = SchemaDiff(
        added_tables={"new_tbl": _table("new_tbl")},
        removed_tables={"old_tbl": _table("old_tbl")},
        modified_tables={"mid": tbl_diff},
    )
    plan = plan_migration(diff)
    actions = [s.action for s in plan.steps]
    assert actions.index("create_table") < actions.index("alter_table")
    assert actions.index("alter_table") < actions.index("drop_table")
