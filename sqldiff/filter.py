"""Filter schemas or diffs by table name patterns."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import List, Optional

from sqldiff.schema import Schema
from sqldiff.differ import SchemaDiff


@dataclass
class FilterOptions:
    include: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)

    def matches(self, table_name: str) -> bool:
        """Return True if *table_name* passes the include/exclude rules."""
        if self.include:
            included = any(fnmatch.fnmatch(table_name, pat) for pat in self.include)
            if not included:
                return False
        if self.exclude:
            excluded = any(fnmatch.fnmatch(table_name, pat) for pat in self.exclude)
            if excluded:
                return False
        return True


def filter_schema(schema: Schema, opts: FilterOptions) -> Schema:
    """Return a new Schema containing only tables that pass *opts*."""
    filtered = {name: tbl for name, tbl in schema.tables.items() if opts.matches(name)}
    return Schema(tables=filtered)


def filter_diff(diff: SchemaDiff, opts: FilterOptions) -> SchemaDiff:
    """Return a new SchemaDiff with only the entries that pass *opts*."""
    return SchemaDiff(
        added={n: t for n, t in diff.added.items() if opts.matches(n)},
        removed={n: t for n, t in diff.removed.items() if opts.matches(n)},
        modified={n: d for n, d in diff.modified.items() if opts.matches(n)},
    )
