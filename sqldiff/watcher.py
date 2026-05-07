"""File system watcher that detects schema file changes and triggers diffs."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional

from sqldiff.loader import load_from_file
from sqldiff.differ import diff_schemas
from sqldiff.schema import Schema


@dataclass
class WatchState:
    """Tracks the last-seen hash and schema for a watched file."""
    path: Path
    checksum: str
    schema: Schema


def _file_checksum(path: Path) -> str:
    """Return MD5 hex-digest of *path* contents."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def _build_state(path: Path) -> WatchState:
    schema = load_from_file(str(path))
    checksum = _file_checksum(path)
    return WatchState(path=path, checksum=checksum, schema=schema)


class SchemaWatcher:
    """Poll one or more SQL schema files and invoke a callback on changes."""

    def __init__(
        self,
        paths: list[str | Path],
        on_change: Callable,
        interval: float = 2.0,
    ) -> None:
        self._paths = [Path(p) for p in paths]
        self._on_change = on_change
        self._interval = interval
        self._states: Dict[Path, WatchState] = {}

    def _initialise(self) -> None:
        for path in self._paths:
            self._states[path] = _build_state(path)

    def _check_once(self) -> None:
        for path in self._paths:
            current_checksum = _file_checksum(path)
            prev = self._states.get(path)
            if prev is None or prev.checksum != current_checksum:
                new_state = _build_state(path)
                old_schema = prev.schema if prev else Schema(tables={})
                diff = diff_schemas(old_schema, new_state.schema)
                self._states[path] = new_state
                self._on_change(path, diff)

    def run_once(self) -> None:
        """Perform a single poll cycle (useful for testing)."""
        if not self._states:
            self._initialise()
            return
        self._check_once()

    def watch(self, max_iterations: Optional[int] = None) -> None:
        """Block and poll until interrupted or *max_iterations* reached."""
        self._initialise()
        count = 0
        try:
            while max_iterations is None or count < max_iterations:
                self._check_once()
                time.sleep(self._interval)
                count += 1
        except KeyboardInterrupt:
            pass
