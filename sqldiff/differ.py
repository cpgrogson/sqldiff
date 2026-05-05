"""Core diffing logic for comparing two Schema snapshots."""

from dataclasses import dataclass, field
from typing import List

from sqldiff.schema import Schema, Table


@dataclass
class SchemaDiff:
    tables_added: List[str] = field(default_factory=list)
    tables_removed: List[str] = field(default_factory=list)
    columns_added: List[str] = field(default_factory=list)
    columns_removed: List[str] = field(default_factory=list)
    columns_modified: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any([
            self.tables_added,
            self.tables_removed,
            self.columns_added,
            self.columns_removed,
            self.columns_modified,
        ])


def _diff_tables(old: Table, new: Table, diff: SchemaDiff) -> None:
    old_cols = set(old.columns.keys())
    new_cols = set(new.columns.keys())

    for col_name in new_cols - old_cols:
        diff.columns_added.append(f"{new.name}.{col_name}")

    for col_name in old_cols - new_cols:
        diff.columns_removed.append(f"{old.name}.{col_name}")

    for col_name in old_cols & new_cols:
        if old.columns[col_name] != new.columns[col_name]:
            diff.columns_modified.append(f"{old.name}.{col_name}")


def diff_schemas(old: Schema, new: Schema) -> SchemaDiff:
    """Compare two Schema objects and return a SchemaDiff."""
    result = SchemaDiff()

    old_tables = set(old.tables.keys())
    new_tables = set(new.tables.keys())

    result.tables_added = sorted(new_tables - old_tables)
    result.tables_removed = sorted(old_tables - new_tables)

    for table_name in old_tables & new_tables:
        _diff_tables(old.tables[table_name], new.tables[table_name], result)

    return result
