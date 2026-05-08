"""Detect and suggest table/column renames based on similarity heuristics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sqldiff.schema import Schema, Table, Column
from sqldiff.differ import SchemaDiff


_DEFAULT_THRESHOLD = 0.6


@dataclass
class RenameCandidate:
    """A suggested rename pairing with a confidence score."""

    old_name: str
    new_name: str
    score: float
    kind: str  # 'table' or 'column'
    table: Optional[str] = None  # set when kind == 'column'

    def __str__(self) -> str:
        if self.kind == "table":
            return f"table {self.old_name!r} -> {self.new_name!r} (score={self.score:.2f})"
        return (
            f"column {self.table}.{self.old_name!r} -> "
            f"{self.table}.{self.new_name!r} (score={self.score:.2f})"
        )


@dataclass
class RenameReport:
    candidates: List[RenameCandidate] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.candidates) == 0

    def tables(self) -> List[RenameCandidate]:
        return [c for c in self.candidates if c.kind == "table"]

    def columns(self) -> List[RenameCandidate]:
        return [c for c in self.candidates if c.kind == "column"]


def _column_similarity(a: Column, b: Column) -> float:
    """Score similarity between two columns (0.0 – 1.0)."""
    score = 0.0
    if a.col_type.upper() == b.col_type.upper():
        score += 0.5
    if a.nullable == b.nullable:
        score += 0.2
    if a.default == b.default:
        score += 0.2
    # partial name match bonus
    an, bn = a.name.lower(), b.name.lower()
    if an in bn or bn in an:
        score += 0.1
    return min(score, 1.0)


def _best_match(
    name: str, candidates: List[str], threshold: float
) -> Optional[Tuple[str, float]]:
    """Return the best Jaccard-like trigram match above *threshold*."""

    def trigrams(s: str):
        s = s.lower()
        return set(s[i : i + 3] for i in range(max(len(s) - 2, 1)))

    ref = trigrams(name)
    best_score = 0.0
    best_name: Optional[str] = None
    for cand in candidates:
        t = trigrams(cand)
        union = ref | t
        sim = len(ref & t) / len(union) if union else 0.0
        if sim > best_score:
            best_score, best_name = sim, cand
    if best_score >= threshold and best_name is not None:
        return best_name, best_score
    return None


def detect_renames(
    diff: SchemaDiff,
    old_schema: Schema,
    new_schema: Schema,
    threshold: float = _DEFAULT_THRESHOLD,
) -> RenameReport:
    """Analyse *diff* and suggest likely renames."""
    report = RenameReport()

    # --- table renames ---
    removed_tables = list(diff.tables_removed)
    added_tables = list(diff.tables_added)
    matched_removed: set = set()
    matched_added: set = set()

    for old_t in removed_tables:
        result = _best_match(old_t, added_tables, threshold)
        if result:
            new_t, score = result
            report.candidates.append(
                RenameCandidate(old_name=old_t, new_name=new_t, score=score, kind="table")
            )
            matched_removed.add(old_t)
            matched_added.add(new_t)

    # --- column renames within common tables ---
    common_tables = set(old_schema.tables) & set(new_schema.tables)
    for tname in common_tables:
        old_cols: Dict[str, Column] = {c.name: c for c in old_schema.tables[tname].columns}
        new_cols: Dict[str, Column] = {c.name: c for c in new_schema.tables[tname].columns}
        removed_cols = [n for n in old_cols if n not in new_cols]
        added_cols = [n for n in new_cols if n not in old_cols]
        for old_c in removed_cols:
            result = _best_match(old_c, added_cols, threshold)
            if result:
                new_c, name_score = result
                col_score = _column_similarity(old_cols[old_c], new_cols[new_c])
                combined = round((name_score + col_score) / 2, 4)
                if combined >= threshold:
                    report.candidates.append(
                        RenameCandidate(
                            old_name=old_c,
                            new_name=new_c,
                            score=combined,
                            kind="column",
                            table=tname,
                        )
                    )

    report.candidates.sort(key=lambda c: c.score, reverse=True)
    return report
