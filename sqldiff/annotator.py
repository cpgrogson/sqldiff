"""Annotate schema diffs with human-readable change descriptions."""
from dataclasses import dataclass, field
from typing import List

from sqldiff.differ import SchemaDiff


@dataclass
class Annotation:
    table: str
    kind: str  # 'table' | 'column' | 'index'
    change: str
    detail: str = ""

    def __str__(self) -> str:
        parts = [f"[{self.kind.upper()}] {self.table}: {self.change}"]
        if self.detail:
            parts.append(f"  → {self.detail}")
        return "\n".join(parts)


@dataclass
class AnnotatedDiff:
    annotations: List[Annotation] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.annotations) == 0

    def by_table(self, table: str) -> List[Annotation]:
        return [a for a in self.annotations if a.table == table]

    def by_kind(self, kind: str) -> List[Annotation]:
        return [a for a in self.annotations if a.kind == kind]


def annotate_diff(diff: SchemaDiff) -> AnnotatedDiff:
    """Produce human-readable annotations for every change in *diff*."""
    result = AnnotatedDiff()

    for table in diff.tables_added:
        col_names = ", ".join(c.name for c in table.columns)
        result.annotations.append(
            Annotation(table.name, "table", "added",
                       f"columns: {col_names}" if col_names else "no columns")
        )

    for table in diff.tables_removed:
        result.annotations.append(
            Annotation(table.name, "table", "removed")
        )

    for td in diff.tables_modified:
        tname = td.name

        for col in td.columns_added:
            detail = col.col_type
            if col.default is not None:
                detail += f", default={col.default}"
            if col.not_null:
                detail += ", NOT NULL"
            result.annotations.append(Annotation(tname, "column", f"'{col.name}' added", detail))

        for col in td.columns_removed:
            result.annotations.append(Annotation(tname, "column", f"'{col.name}' removed"))

        for cd in td.columns_modified:
            changes = []
            if cd.old_type != cd.new_type:
                changes.append(f"type {cd.old_type!r} → {cd.new_type!r}")
            if cd.old_default != cd.new_default:
                changes.append(f"default {cd.old_default!r} → {cd.new_default!r}")
            if cd.old_not_null != cd.new_not_null:
                changes.append(f"not_null {cd.old_not_null} → {cd.new_not_null}")
            result.annotations.append(
                Annotation(tname, "column", f"'{cd.name}' modified", "; ".join(changes))
            )

        for idx in getattr(td, "indexes_added", []):
            result.annotations.append(
                Annotation(tname, "index", f"'{idx.name}' added",
                           f"columns: {', '.join(idx.columns)}")
            )

        for idx in getattr(td, "indexes_removed", []):
            result.annotations.append(
                Annotation(tname, "index", f"'{idx.name}' removed")
            )

    return result
