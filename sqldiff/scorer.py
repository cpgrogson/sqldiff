"""Similarity scorer: computes a numeric similarity score between two schemas."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqldiff.schema import Schema

from sqldiff.differ import SchemaDiff


@dataclass
class SimilarityScore:
    """Holds the result of comparing two schemas."""

    total_objects: int
    changed_objects: int
    score: float  # 0.0 (completely different) – 1.0 (identical)

    def __str__(self) -> str:  # pragma: no cover
        pct = round(self.score * 100, 1)
        return (
            f"Similarity: {pct}% "
            f"({self.changed_objects} change(s) across {self.total_objects} object(s))"
        )


def _count_changes(diff: SchemaDiff) -> int:
    """Return the total number of distinct change events in *diff*."""
    changes = 0
    changes += len(diff.tables_added)
    changes += len(diff.tables_removed)
    for td in diff.tables_modified:
        changes += len(td.columns_added)
        changes += len(td.columns_removed)
        changes += len(td.columns_modified)
        changes += len(td.indexes_added)
        changes += len(td.indexes_removed)
    return changes


def _count_objects(old: "Schema", new: "Schema") -> int:
    """Return the total number of unique table names across both schemas."""
    all_tables = set(old.tables) | set(new.tables)
    return max(len(all_tables), 1)  # avoid division by zero


def score_schemas(old: "Schema", new: "Schema", diff: SchemaDiff) -> SimilarityScore:
    """Compute a similarity score between *old* and *new* using a pre-built *diff*.

    The score is ``1 - (changes / total_objects)`` clamped to ``[0.0, 1.0]``.
    """
    total = _count_objects(old, new)
    changes = _count_changes(diff)
    raw = 1.0 - changes / total
    score = max(0.0, min(1.0, raw))
    return SimilarityScore(
        total_objects=total,
        changed_objects=changes,
        score=round(score, 4),
    )
