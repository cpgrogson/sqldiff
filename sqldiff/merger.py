"""Merge two schemas into a unified schema, preferring changes from the 'new' side."""

from dataclasses import dataclass, field
from typing import List

from sqldiff.schema import Schema, Table, Column, Index


@dataclass
class MergeConflict:
    table_name: str
    column_name: str
    base_value: str
    other_value: str

    def __str__(self) -> str:
        return (
            f"Conflict in {self.table_name}.{self.column_name}: "
            f"base={self.base_value!r} vs other={self.other_value!r}"
        )


@dataclass
class MergeResult:
    schema: Schema
    conflicts: List[MergeConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0


def _merge_columns(base: List[Column], other: List[Column], table_name: str,
                   conflicts: List[MergeConflict]) -> List[Column]:
    base_map = {c.name: c for c in base}
    other_map = {c.name: c for c in other}
    merged = []

    all_names = list(base_map) + [n for n in other_map if n not in base_map]
    for name in all_names:
        if name in base_map and name in other_map:
            b, o = base_map[name], other_map[name]
            if b.col_type != o.col_type:
                conflicts.append(MergeConflict(table_name, name, b.col_type, o.col_type))
            # Prefer 'other' on conflict
            merged.append(o)
        elif name in other_map:
            merged.append(other_map[name])
        else:
            merged.append(base_map[name])
    return merged


def _merge_indexes(base: List[Index], other: List[Index]) -> List[Index]:
    base_map = {i.name: i for i in base}
    other_map = {i.name: i for i in other}
    merged = {**base_map, **other_map}  # other wins
    return list(merged.values())


def merge_schemas(base: Schema, other: Schema) -> MergeResult:
    """Merge *other* into *base*, returning a MergeResult with the unified schema."""
    conflicts: List[MergeConflict] = []
    base_tables = {t.name: t for t in base.tables}
    other_tables = {t.name: t for t in other.tables}

    merged_tables: List[Table] = []
    all_names = list(base_tables) + [n for n in other_tables if n not in base_tables]

    for name in all_names:
        if name in base_tables and name in other_tables:
            bt, ot = base_tables[name], other_tables[name]
            merged_cols = _merge_columns(bt.columns, ot.columns, name, conflicts)
            merged_idx = _merge_indexes(bt.indexes, ot.indexes)
            merged_tables.append(Table(name=name, columns=merged_cols, indexes=merged_idx))
        elif name in other_tables:
            merged_tables.append(other_tables[name])
        else:
            merged_tables.append(base_tables[name])

    return MergeResult(schema=Schema(tables=merged_tables), conflicts=conflicts)
