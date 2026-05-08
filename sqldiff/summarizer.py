"""Summarizer: produce human-readable statistics for a SchemaDiff."""
from dataclasses import dataclass
from typing import Dict

from sqldiff.differ import SchemaDiff


@dataclass
class DiffStats:
    tables_added: int = 0
    tables_removed: int = 0
    tables_modified: int = 0
    columns_added: int = 0
    columns_removed: int = 0
    columns_modified: int = 0
    indexes_added: int = 0
    indexes_removed: int = 0

    @property
    def total_changes(self) -> int:
        return (
            self.tables_added
            + self.tables_removed
            + self.tables_modified
            + self.columns_added
            + self.columns_removed
            + self.columns_modified
            + self.indexes_added
            + self.indexes_removed
        )

    def to_dict(self) -> Dict[str, int]:
        return {
            "tables_added": self.tables_added,
            "tables_removed": self.tables_removed,
            "tables_modified": self.tables_modified,
            "columns_added": self.columns_added,
            "columns_removed": self.columns_removed,
            "columns_modified": self.columns_modified,
            "indexes_added": self.indexes_added,
            "indexes_removed": self.indexes_removed,
            "total_changes": self.total_changes,
        }

    def __str__(self) -> str:
        lines = [
            f"Tables  : +{self.tables_added} / -{self.tables_removed} / ~{self.tables_modified}",
            f"Columns : +{self.columns_added} / -{self.columns_removed} / ~{self.columns_modified}",
            f"Indexes : +{self.indexes_added} / -{self.indexes_removed}",
            f"Total   : {self.total_changes} change(s)",
        ]
        return "\n".join(lines)


def summarize(diff: SchemaDiff) -> DiffStats:
    """Compute a DiffStats summary from a SchemaDiff."""
    stats = DiffStats()
    stats.tables_added = len(diff.tables_added)
    stats.tables_removed = len(diff.tables_removed)

    for table_diff in diff.tables_modified:
        has_col_change = (
            bool(table_diff.columns_added)
            or bool(table_diff.columns_removed)
            or bool(table_diff.columns_modified)
        )
        has_idx_change = bool(table_diff.indexes_added) or bool(table_diff.indexes_removed)
        if has_col_change or has_idx_change:
            stats.tables_modified += 1

        stats.columns_added += len(table_diff.columns_added)
        stats.columns_removed += len(table_diff.columns_removed)
        stats.columns_modified += len(table_diff.columns_modified)
        stats.indexes_added += len(table_diff.indexes_added)
        stats.indexes_removed += len(table_diff.indexes_removed)

    return stats
