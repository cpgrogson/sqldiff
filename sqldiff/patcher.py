"""Schema patcher: apply a SchemaDiff to a base Schema to produce a patched Schema.

This module provides a pure-Python way to replay the changes recorded in a
``SchemaDiff`` onto an existing ``Schema`` object without touching a real
database.  It is useful for preview, testing, and pipeline composition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sqldiff.schema import Column, Index, Schema, Table
from sqldiff.differ import SchemaDiff


@dataclass
class PatchResult:
    """Outcome of applying a diff to a schema."""

    schema: Schema
    applied: List[str] = field(default_factory=list)   # human-readable log
    skipped: List[str] = field(default_factory=list)   # warnings / skipped ops

    @property
    def is_clean(self) -> bool:
        """True when every change was applied without skips."""
        return len(self.skipped) == 0

    def __str__(self) -> str:  # pragma: no cover
        lines = [f"Applied {len(self.applied)} change(s), skipped {len(self.skipped)}."]
        for msg in self.applied:
            lines.append(f"  + {msg}")
        for msg in self.skipped:
            lines.append(f"  ! {msg}")
        return "\n".join(lines)


def _copy_table(table: Table) -> Table:
    """Return a shallow copy of *table* with independent column/index lists."""
    return Table(
        name=table.name,
        columns=list(table.columns),
        indexes=list(table.indexes),
    )


def patch_schema(base: Schema, diff: SchemaDiff) -> PatchResult:
    """Apply *diff* to *base* and return a :class:`PatchResult`.

    The original *base* schema is **not** mutated; a new :class:`Schema` is
    built and returned inside the result.

    Parameters
    ----------
    base:
        The starting-point schema (the "old" side of the diff).
    diff:
        A :class:`~sqldiff.differ.SchemaDiff` produced by
        :func:`~sqldiff.differ.diff_schemas`.

    Returns
    -------
    PatchResult
        Contains the patched schema plus an audit log of every operation.
    """
    # Work with a mutable dict of Table copies keyed by name.
    tables: dict[str, Table] = {t.name: _copy_table(t) for t in base.tables}
    applied: list[str] = []
    skipped: list[str] = []

    # --- tables added in the diff ----------------------------------------
    for table in diff.tables_added:
        if table.name in tables:
            skipped.append(
                f"Table '{table.name}' already exists in base – skipped ADD."
            )
        else:
            tables[table.name] = _copy_table(table)
            applied.append(f"Added table '{table.name}'.")

    # --- tables removed in the diff --------------------------------------
    for table in diff.tables_removed:
        if table.name not in tables:
            skipped.append(
                f"Table '{table.name}' not found in base – skipped REMOVE."
            )
        else:
            del tables[table.name]
            applied.append(f"Removed table '{table.name}'.")

    # --- column-level changes inside modified tables ---------------------
    for table_diff in diff.tables_modified:
        tname = table_diff.table_name
        if tname not in tables:
            skipped.append(
                f"Table '{tname}' not found in base – skipped column patches."
            )
            continue

        tbl = tables[tname]
        col_map: dict[str, Column] = {c.name: c for c in tbl.columns}

        for col in table_diff.columns_added:
            if col.name in col_map:
                skipped.append(
                    f"Column '{tname}.{col.name}' already exists – skipped ADD."
                )
            else:
                col_map[col.name] = col
                applied.append(f"Added column '{tname}.{col.name}'.")

        for col in table_diff.columns_removed:
            if col.name not in col_map:
                skipped.append(
                    f"Column '{tname}.{col.name}' not found – skipped REMOVE."
                )
            else:
                del col_map[col.name]
                applied.append(f"Removed column '{tname}.{col.name}'.")

        for col_change in table_diff.columns_modified:
            cname = col_change.new.name
            if cname not in col_map:
                skipped.append(
                    f"Column '{tname}.{cname}' not found – skipped MODIFY."
                )
            else:
                col_map[cname] = col_change.new
                applied.append(f"Modified column '{tname}.{cname}'.")

        # Preserve original column order; append new columns at the end.
        original_order = [c.name for c in tbl.columns]
        ordered = [col_map[n] for n in original_order if n in col_map]
        new_cols = [col_map[n] for n in col_map if n not in set(original_order)]
        tables[tname] = Table(
            name=tname,
            columns=ordered + new_cols,
            indexes=list(tbl.indexes),
        )

    patched_schema = Schema(tables=list(tables.values()))
    return PatchResult(schema=patched_schema, applied=applied, skipped=skipped)
