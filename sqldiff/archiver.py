"""Archive and retrieve historical diff snapshots with metadata."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sqldiff.differ import SchemaDiff
from sqldiff.formatter import format_json

_ARCHIVE_VERSION = 1
_INDEX_FILE = "archive_index.json"


@dataclass
class ArchiveEntry:
    archive_id: str
    created_at: str
    label: Optional[str]
    tables_added: int
    tables_removed: int
    tables_modified: int

    def __str__(self) -> str:
        label_part = f" [{self.label}]" if self.label else ""
        return (
            f"{self.archive_id}{label_part} @ {self.created_at} "
            f"(+{self.tables_added}/-{self.tables_removed}/~{self.tables_modified})"
        )


@dataclass
class ArchiveIndex:
    version: int = _ARCHIVE_VERSION
    entries: List[ArchiveEntry] = field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _archive_dir(base_dir: str | Path) -> Path:
    return Path(base_dir)


def _load_index(base_dir: Path) -> ArchiveIndex:
    index_path = base_dir / _INDEX_FILE
    if not index_path.exists():
        return ArchiveIndex()
    with index_path.open() as fh:
        raw = json.load(fh)
    entries = [
        ArchiveEntry(
            archive_id=e["archive_id"],
            created_at=e["created_at"],
            label=e.get("label"),
            tables_added=e["tables_added"],
            tables_removed=e["tables_removed"],
            tables_modified=e["tables_modified"],
        )
        for e in raw.get("entries", [])
    ]
    return ArchiveIndex(version=raw.get("version", _ARCHIVE_VERSION), entries=entries)


def _save_index(base_dir: Path, index: ArchiveIndex) -> None:
    index_path = base_dir / _INDEX_FILE
    payload = {
        "version": index.version,
        "entries": [
            {
                "archive_id": e.archive_id,
                "created_at": e.created_at,
                "label": e.label,
                "tables_added": e.tables_added,
                "tables_removed": e.tables_removed,
                "tables_modified": e.tables_modified,
            }
            for e in index.entries
        ],
    }
    with index_path.open("w") as fh:
        json.dump(payload, fh, indent=2)


def archive_diff(
    diff: SchemaDiff,
    base_dir: str | Path,
    label: Optional[str] = None,
) -> ArchiveEntry:
    """Persist *diff* to *base_dir* and return the created ArchiveEntry."""
    base_dir = _archive_dir(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    archive_id = _now_iso()
    diff_path = base_dir / f"{archive_id}.json"
    diff_path.write_text(format_json(diff))

    entry = ArchiveEntry(
        archive_id=archive_id,
        created_at=archive_id,
        label=label,
        tables_added=len(diff.added),
        tables_removed=len(diff.removed),
        tables_modified=len(diff.modified),
    )
    index = _load_index(base_dir)
    index.entries.append(entry)
    _save_index(base_dir, index)
    return entry


def list_archives(base_dir: str | Path) -> List[ArchiveEntry]:
    """Return all archived entries sorted newest-first."""
    index = _load_index(_archive_dir(base_dir))
    return list(reversed(index.entries))


def load_archive(base_dir: str | Path, archive_id: str) -> str:
    """Return the raw JSON text for a previously archived diff."""
    diff_path = _archive_dir(base_dir) / f"{archive_id}.json"
    if not diff_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_id}")
    return diff_path.read_text()
