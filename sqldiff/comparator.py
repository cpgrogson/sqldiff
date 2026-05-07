"""Column and index-level comparator utilities for detailed schema diffing."""

from dataclasses import dataclass, field
from typing import List

from sqldiff.schema import Column, Index, Table


@dataclass
class ColumnDiff:
    name: str
    old: Column
    new: Column
    changes: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.old.type != self.new.type:
            self.changes.append(f"type: {self.old.type!r} -> {self.new.type!r}")
        if self.old.nullable != self.new.nullable:
            self.changes.append(f"nullable: {self.old.nullable} -> {self.new.nullable}")
        if self.old.default != self.new.default:
            self.changes.append(f"default: {self.old.default!r} -> {self.new.default!r}")

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)


@dataclass
class IndexDiff:
    name: str
    old: Index
    new: Index
    changes: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.old.columns != self.new.columns:
            self.changes.append(f"columns: {self.old.columns} -> {self.new.columns}")
        if self.old.unique != self.new.unique:
            self.changes.append(f"unique: {self.old.unique} -> {self.new.unique}")

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)


@dataclass
class TableComparison:
    table_name: str
    added_columns: List[Column] = field(default_factory=list)
    removed_columns: List[Column] = field(default_factory=list)
    modified_columns: List[ColumnDiff] = field(default_factory=list)
    added_indexes: List[Index] = field(default_factory=list)
    removed_indexes: List[Index] = field(default_factory=list)
    modified_indexes: List[IndexDiff] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any([
            self.added_columns, self.removed_columns, self.modified_columns,
            self.added_indexes, self.removed_indexes, self.modified_indexes,
        ])


def compare_tables(old: Table, new: Table) -> TableComparison:
    """Return a detailed comparison between two versions of the same table."""
    result = TableComparison(table_name=old.name)

    old_cols = {c.name: c for c in old.columns}
    new_cols = {c.name: c for c in new.columns}

    for name, col in new_cols.items():
        if name not in old_cols:
            result.added_columns.append(col)
        else:
            diff = ColumnDiff(name=name, old=old_cols[name], new=col)
            if diff.has_changes:
                result.modified_columns.append(diff)

    for name, col in old_cols.items():
        if name not in new_cols:
            result.removed_columns.append(col)

    old_idx = {i.name: i for i in old.indexes}
    new_idx = {i.name: i for i in new.indexes}

    for name, idx in new_idx.items():
        if name not in old_idx:
            result.added_indexes.append(idx)
        else:
            diff = IndexDiff(name=name, old=old_idx[name], new=idx)
            if diff.has_changes:
                result.modified_indexes.append(diff)

    for name, idx in old_idx.items():
        if name not in new_idx:
            result.removed_indexes.append(idx)

    return result
