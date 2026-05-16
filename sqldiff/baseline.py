"""Baseline management: mark a diff as the accepted baseline and detect drift."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sqldiff.differ import SchemaDiff


@dataclass
class BaselineMeta:
    created_at: str
    label: Optional[str]
    added_tables: List[str]
    removed_tables: List[str]
    modified_tables: List[str]

    def to_dict(self) -> dict:
        return {
            "created_at": self.created_at,
            "label": self.label,
            "added_tables": self.added_tables,
            "removed_tables": self.removed_tables,
            "modified_tables": self.modified_tables,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BaselineMeta":
        return cls(
            created_at=data["created_at"],
            label=data.get("label"),
            added_tables=data.get("added_tables", []),
            removed_tables=data.get("removed_tables", []),
            modified_tables=data.get("modified_tables", []),
        )

    def __str__(self) -> str:
        parts = [f"Baseline({self.created_at}"]
        if self.label:
            parts.append(f" label={self.label!r}")
        parts.append(")")
        return "".join(parts)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _baseline_path(directory: str) -> Path:
    return Path(directory) / ".sqldiff_baseline.json"


def save_baseline(diff: SchemaDiff, directory: str, label: Optional[str] = None) -> BaselineMeta:
    """Persist *diff* as the accepted baseline inside *directory*."""
    meta = BaselineMeta(
        created_at=_now_iso(),
        label=label,
        added_tables=sorted(diff.added_tables),
        removed_tables=sorted(diff.removed_tables),
        modified_tables=sorted(diff.modified_tables.keys()),
    )
    path = _baseline_path(directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta.to_dict(), indent=2), encoding="utf-8")
    return meta


def load_baseline(directory: str) -> BaselineMeta:
    """Load the baseline stored in *directory*; raises FileNotFoundError if absent."""
    path = _baseline_path(directory)
    if not path.exists():
        raise FileNotFoundError(f"No baseline found in {directory!r}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return BaselineMeta.from_dict(data)


def diff_from_baseline(diff: SchemaDiff, directory: str) -> dict:
    """Return tables in *diff* that are NOT covered by the stored baseline.

    Returns a dict with keys 'new_added', 'new_removed', 'new_modified'.
    """
    baseline = load_baseline(directory)
    return {
        "new_added": [t for t in diff.added_tables if t not in baseline.added_tables],
        "new_removed": [t for t in diff.removed_tables if t not in baseline.removed_tables],
        "new_modified": [
            t for t in diff.modified_tables if t not in baseline.modified_tables
        ],
    }
