"""Trace column lineage across schema versions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqldiff.schema import Schema


@dataclass
class ColumnLineage:
    """Tracks a single column's history across snapshots."""
    table: str
    column: str
    history: List[Dict] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.table}.{self.column} ({len(self.history)} snapshot(s))"

    def added_in(self) -> Optional[str]:
        """Return label of snapshot where column first appeared."""
        for entry in self.history:
            if entry.get("status") == "added":
                return entry.get("snapshot")
        return None

    def removed_in(self) -> Optional[str]:
        """Return label of snapshot where column was removed."""
        for entry in self.history:
            if entry.get("status") == "removed":
                return entry.get("snapshot")
        return None


@dataclass
class TraceReport:
    """Aggregated lineage for all traced columns."""
    lineages: List[ColumnLineage] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.lineages) == 0

    def for_table(self, table: str) -> List[ColumnLineage]:
        return [ln for ln in self.lineages if ln.table == table]

    def __str__(self) -> str:
        if self.is_empty():
            return "TraceReport: no lineage data"
        lines = [f"TraceReport: {len(self.lineages)} column(s) traced"]
        for ln in self.lineages:
            lines.append(f"  {ln}")
        return "\n".join(lines)


def trace_column(
    snapshots: List[Dict[str, Schema]],
    table: str,
    column: str,
) -> ColumnLineage:
    """Trace a specific column across an ordered list of labelled snapshots.

    Each element of *snapshots* is a dict with a single key (the label) mapping
    to a :class:`~sqldiff.schema.Schema`.
    """
    lineage = ColumnLineage(table=table, column=column)
    prev_col = None
    for snap in snapshots:
        label, schema = next(iter(snap.items()))
        tbl = schema.tables.get(table)
        cur_col = tbl.columns.get(column) if tbl else None
        if cur_col is None and prev_col is not None:
            lineage.history.append({"snapshot": label, "status": "removed", "column": None})
        elif cur_col is not None and prev_col is None:
            lineage.history.append({"snapshot": label, "status": "added", "column": cur_col})
        elif cur_col is not None and prev_col is not None and cur_col != prev_col:
            lineage.history.append({"snapshot": label, "status": "modified", "column": cur_col})
        else:
            lineage.history.append({"snapshot": label, "status": "unchanged", "column": cur_col})
        prev_col = cur_col
    return lineage


def trace_schema(snapshots: List[Dict[str, Schema]]) -> TraceReport:
    """Trace all columns found across all snapshots."""
    seen: set = set()
    for snap in snapshots:
        _, schema = next(iter(snap.items()))
        for tname, tbl in schema.tables.items():
            for cname in tbl.columns:
                seen.add((tname, cname))
    lineages = [
        trace_column(snapshots, tname, cname)
        for tname, cname in sorted(seen)
    ]
    return TraceReport(lineages=lineages)
