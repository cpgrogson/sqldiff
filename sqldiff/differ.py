"""Diff two Schema objects and produce a SchemaDiff summary."""

from dataclasses import dataclass, field
from typing import Dict, List

from sqldiff.schema import Schema, Table
from sqldiff.comparator import TableComparison, compare_tables


@dataclass
class SchemaDiff:
    added_tables: List[Table] = field(default_factory=list)
    removed_tables: List[Table] = field(default_factory=list)
    modified_tables: List[TableComparison] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added_tables or self.removed_tables or self.modified_tables)

    def summary(self) -> str:
        parts = []
        if self.added_tables:
            names = ", ".join(t.name for t in self.added_tables)
            parts.append(f"Added tables: {names}")
        if self.removed_tables:
            names = ", ".join(t.name for t in self.removed_tables)
            parts.append(f"Removed tables: {names}")
        if self.modified_tables:
            names = ", ".join(tc.table_name for tc in self.modified_tables)
            parts.append(f"Modified tables: {names}")
        return "; ".join(parts) if parts else "No changes"


def _diff_tables(old: Table, new: Table) -> TableComparison:
    """Delegate detailed table comparison to the comparator module."""
    return compare_tables(old, new)


def diff_schemas(old: Schema, new: Schema) -> SchemaDiff:
    """Compare two Schema objects and return a SchemaDiff."""
    result = SchemaDiff()

    old_tables: Dict[str, Table] = {t.name: t for t in old.tables}
    new_tables: Dict[str, Table] = {t.name: t for t in new.tables}

    for name, table in new_tables.items():
        if name not in old_tables:
            result.added_tables.append(table)
        else:
            comparison = _diff_tables(old_tables[name], table)
            if comparison.has_changes:
                result.modified_tables.append(comparison)

    for name, table in old_tables.items():
        if name not in new_tables:
            result.removed_tables.append(table)

    return result
