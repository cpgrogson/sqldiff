"""Aggregated statistics derived from a SchemaDiff, suitable for reporting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from sqldiff.differ import SchemaDiff


@dataclass
class TableStats:
    name: str
    columns_added: int = 0
    columns_removed: int = 0
    columns_modified: int = 0
    indexes_added: int = 0
    indexes_removed: int = 0

    @property
    def total(self) -> int:
        return (
            self.columns_added
            + self.columns_removed
            + self.columns_modified
            + self.indexes_added
            + self.indexes_removed
        )

    def to_dict(self) -> Dict:
        return {
            "table": self.name,
            "columns_added": self.columns_added,
            "columns_removed": self.columns_removed,
            "columns_modified": self.columns_modified,
            "indexes_added": self.indexes_added,
            "indexes_removed": self.indexes_removed,
            "total": self.total,
        }


@dataclass
class DiffStatReport:
    tables_added: List[str] = field(default_factory=list)
    tables_removed: List[str] = field(default_factory=list)
    table_stats: List[TableStats] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return (
            len(self.tables_added)
            + len(self.tables_removed)
            + sum(ts.total for ts in self.table_stats)
        )

    def to_dict(self) -> Dict:
        return {
            "tables_added": self.tables_added,
            "tables_removed": self.tables_removed,
            "table_changes": [ts.to_dict() for ts in self.table_stats],
            "total_changes": self.total_changes,
        }

    def __str__(self) -> str:
        lines = [f"Total changes: {self.total_changes}"]
        if self.tables_added:
            lines.append(f"  Tables added:   {', '.join(self.tables_added)}")
        if self.tables_removed:
            lines.append(f"  Tables removed: {', '.join(self.tables_removed)}")
        for ts in self.table_stats:
            if ts.total:
                lines.append(f"  {ts.name}: {ts.total} change(s)")
        return "\n".join(lines)


def build_stat_report(diff: SchemaDiff) -> DiffStatReport:
    """Build a DiffStatReport from a SchemaDiff."""
    report = DiffStatReport(
        tables_added=list(diff.tables_added),
        tables_removed=list(diff.tables_removed),
    )
    for tname, tdiff in diff.tables_modified.items():
        ts = TableStats(name=tname)
        ts.columns_added = len(tdiff.columns_added)
        ts.columns_removed = len(tdiff.columns_removed)
        ts.columns_modified = len(tdiff.columns_modified)
        ts.indexes_added = len(tdiff.indexes_added)
        ts.indexes_removed = len(tdiff.indexes_removed)
        if ts.total:
            report.table_stats.append(ts)
    return report
