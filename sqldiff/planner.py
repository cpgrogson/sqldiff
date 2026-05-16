"""Migration planner: orders migration steps and detects dependency conflicts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqldiff.differ import SchemaDiff
from sqldiff.grapher import SchemaGraph, build_graph


@dataclass
class PlanStep:
    order: int
    action: str          # 'create_table' | 'drop_table' | 'alter_table'
    table: str
    detail: Optional[str] = None

    def __str__(self) -> str:
        suffix = f" — {self.detail}" if self.detail else ""
        return f"[{self.order:02d}] {self.action} {self.table}{suffix}"


@dataclass
class MigrationPlan:
    steps: List[PlanStep] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.steps) == 0

    def __str__(self) -> str:
        if self.is_empty():
            return "No migration steps."
        lines = [str(s) for s in self.steps]
        if self.warnings:
            lines.append("")
            lines.extend(f"WARNING: {w}" for w in self.warnings)
        return "\n".join(lines)


def plan_migration(diff: SchemaDiff) -> MigrationPlan:
    """Produce an ordered MigrationPlan from a SchemaDiff.

    Tables are created in topological (FK-dependency) order and dropped in
    reverse order so that referential integrity is preserved.
    """
    steps: List[PlanStep] = []
    warnings: List[str] = []
    counter = 1

    # Determine creation order using the *new* schema graph.
    if diff.added_tables:
        try:
            graph = build_graph(diff.added_tables)
            ordered = graph.tables_in_order()
        except Exception:  # cycle or missing FK target — fall back to sorted
            ordered = sorted(diff.added_tables.keys())
            warnings.append("Could not resolve FK order for added tables; using alphabetical order.")
        for name in ordered:
            if name in diff.added_tables:
                steps.append(PlanStep(counter, "create_table", name))
                counter += 1

    # Altered tables come next.
    for name, tbl_diff in sorted(diff.modified_tables.items()):
        added_cols = len(tbl_diff.added_columns)
        removed_cols = len(tbl_diff.removed_columns)
        changed_cols = len(tbl_diff.modified_columns)
        detail = f"+{added_cols} col(s), -{removed_cols} col(s), ~{changed_cols} col(s)"
        steps.append(PlanStep(counter, "alter_table", name, detail))
        counter += 1

    # Removed tables are dropped in reverse dependency order.
    if diff.removed_tables:
        try:
            graph = build_graph(diff.removed_tables)
            ordered_drop = list(reversed(graph.tables_in_order()))
        except Exception:
            ordered_drop = sorted(diff.removed_tables.keys(), reverse=True)
            warnings.append("Could not resolve FK order for removed tables; using reverse-alphabetical order.")
        for name in ordered_drop:
            if name in diff.removed_tables:
                steps.append(PlanStep(counter, "drop_table", name))
                counter += 1

    return MigrationPlan(steps=steps, warnings=warnings)
