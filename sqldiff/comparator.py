"""Fine-grained column- and index-level diff structures."""
from dataclasses import dataclass, field
from typing import List, Optional

from sqldiff.schema import Column, Index, Table


@dataclass
class ColumnDiff:
    name: str
    old_type: str
    new_type: str
    old_default: Optional[str]
    new_default: Optional[str]
    old_not_null: bool
    new_not_null: bool

    def __post_init__(self):
        if not self.name:
            raise ValueError("ColumnDiff.name must not be empty")

    def has_changes(self) -> bool:
        return (
            self.old_type != self.new_type
            or self.old_default != self.new_default
            or self.old_not_null != self.new_not_null
        )


@dataclass
class IndexDiff:
    name: str
    old_columns: List[str]
    new_columns: List[str]
    old_unique: bool
    new_unique: bool

    def __post_init__(self):
        if not self.name:
            raise ValueError("IndexDiff.name must not be empty")

    def has_changes(self) -> bool:
        return self.old_columns != self.new_columns or self.old_unique != self.new_unique


@dataclass
class TableDiff:
    name: str
    columns_added: List[Column] = field(default_factory=list)
    columns_removed: List[Column] = field(default_factory=list)
    columns_modified: List[ColumnDiff] = field(default_factory=list)
    indexes_added: List[Index] = field(default_factory=list)
    indexes_removed: List[Index] = field(default_factory=list)
    indexes_modified: List[IndexDiff] = field(default_factory=list)

    def has_changes(self) -> bool:
        return any([
            self.columns_added,
            self.columns_removed,
            self.columns_modified,
            self.indexes_added,
            self.indexes_removed,
            self.indexes_modified,
        ])


def _compare_columns(old: Column, new: Column) -> Optional[ColumnDiff]:
    cd = ColumnDiff(
        name=old.name,
        old_type=old.col_type, new_type=new.col_type,
        old_default=old.default, new_default=new.default,
        old_not_null=old.not_null, new_not_null=new.not_null,
    )
    return cd if cd.has_changes() else None


def _compare_indexes(old: Index, new: Index) -> Optional[IndexDiff]:
    id_ = IndexDiff(
        name=old.name,
        old_columns=old.columns, new_columns=new.columns,
        old_unique=old.unique, new_unique=new.unique,
    )
    return id_ if id_.has_changes() else None


def compare_tables(old: Table, new: Table) -> TableDiff:
    """Return a TableDiff describing all changes between *old* and *new*."""
    old_cols = {c.name: c for c in old.columns}
    new_cols = {c.name: c for c in new.columns}

    cols_added = [new_cols[n] for n in new_cols if n not in old_cols]
    cols_removed = [old_cols[n] for n in old_cols if n not in new_cols]
    cols_modified = [
        diff for n in old_cols if n in new_cols
        for diff in [_compare_columns(old_cols[n], new_cols[n])] if diff
    ]

    old_idx = {i.name: i for i in old.indexes}
    new_idx = {i.name: i for i in new.indexes}

    idx_added = [new_idx[n] for n in new_idx if n not in old_idx]
    idx_removed = [old_idx[n] for n in old_idx if n not in new_idx]
    idx_modified = [
        diff for n in old_idx if n in new_idx
        for diff in [_compare_indexes(old_idx[n], new_idx[n])] if diff
    ]

    return TableDiff(
        name=old.name,
        columns_added=cols_added, columns_removed=cols_removed, columns_modified=cols_modified,
        indexes_added=idx_added, indexes_removed=idx_removed, indexes_modified=idx_modified,
    )
