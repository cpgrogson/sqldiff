"""Snapshot management: save and load named schema snapshots."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqldiff.loader import load_from_string
from sqldiff.schema import Schema

_SNAPSHOT_EXT = ".snap.json"


@dataclass
class SnapshotMeta:
    name: str
    created_at: str
    sql_source: str

    @staticmethod
    def now(name: str, sql_source: str) -> "SnapshotMeta":
        ts = datetime.now(timezone.utc).isoformat()
        return SnapshotMeta(name=name, created_at=ts, sql_source=sql_source)


def _snapshot_path(directory: str, name: str) -> str:
    safe = name.replace(os.sep, "_")
    return os.path.join(directory, safe + _SNAPSHOT_EXT)


def save_snapshot(directory: str, name: str, sql_source: str) -> str:
    """Persist a SQL schema string as a named snapshot.

    Returns the path of the written file.
    """
    os.makedirs(directory, exist_ok=True)
    meta = SnapshotMeta.now(name, sql_source)
    payload = asdict(meta)
    path = _snapshot_path(directory, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return path


def load_snapshot(directory: str, name: str) -> Schema:
    """Load a previously saved snapshot and return a Schema object."""
    path = _snapshot_path(directory, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Snapshot '{name}' not found at {path}")
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    sql_source = payload["sql_source"]
    return load_from_string(sql_source)


def list_snapshots(directory: str) -> List[SnapshotMeta]:
    """Return metadata for all snapshots stored in *directory*."""
    if not os.path.isdir(directory):
        return []
    results: List[SnapshotMeta] = []
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(_SNAPSHOT_EXT):
            continue
        fpath = os.path.join(directory, fname)
        with open(fpath, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        results.append(SnapshotMeta(**payload))
    return results


def delete_snapshot(directory: str, name: str) -> bool:
    """Delete a snapshot by name. Returns True if deleted, False if not found."""
    path = _snapshot_path(directory, name)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
