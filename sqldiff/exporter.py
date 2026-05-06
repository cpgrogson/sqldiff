"""Export schema diffs to various file formats."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Union

from sqldiff.differ import SchemaDiff
from sqldiff.formatter import format_text, format_json


SUPPORTED_FORMATS = ("text", "json", "sql")


def _diff_to_sql(diff: SchemaDiff) -> str:
    """Render a SchemaDiff as a series of DDL ALTER / CREATE / DROP statements."""
    lines: list[str] = []

    for table_name in diff.tables_added:
        lines.append(f"-- Table added: {table_name}")
        lines.append(f"-- (full CREATE TABLE statement not available in diff)")
        lines.append("")

    for table_name in diff.tables_removed:
        lines.append(f"DROP TABLE IF EXISTS {table_name};")
        lines.append("")

    for table_name, table_diff in diff.tables_changed.items():
        for col in table_diff.get("columns_added", []):
            col_def = f"{col.name} {col.col_type}"
            if not col.nullable:
                col_def += " NOT NULL"
            if col.default is not None:
                col_def += f" DEFAULT {col.default}"
            lines.append(f"ALTER TABLE {table_name} ADD COLUMN {col_def};")

        for col in table_diff.get("columns_removed", []):
            lines.append(f"ALTER TABLE {table_name} DROP COLUMN {col.name};")

        for col_name, changes in table_diff.get("columns_changed", {}).items():
            for field, (old_val, new_val) in changes.items():
                lines.append(
                    f"-- ALTER TABLE {table_name} MODIFY COLUMN {col_name}"
                    f" {field}: {old_val!r} -> {new_val!r}"
                )

        for idx in table_diff.get("indexes_added", []):
            unique = "UNIQUE " if idx.unique else ""
            cols = ", ".join(idx.columns)
            lines.append(
                f"CREATE {unique}INDEX {idx.name} ON {table_name} ({cols});"
            )

        for idx in table_diff.get("indexes_removed", []):
            lines.append(f"DROP INDEX IF EXISTS {idx.name};")

        if lines and lines[-1] != "":
            lines.append("")

    return "\n".join(lines).strip()


def export_diff(
    diff: SchemaDiff,
    destination: Union[str, Path],
    fmt: str = "text",
) -> Path:
    """Write *diff* to *destination* in the requested format.

    Parameters
    ----------
    diff:        The computed schema diff.
    destination: File path to write output to.
    fmt:         One of ``'text'``, ``'json'``, or ``'sql'``.

    Returns
    -------
    The resolved :class:`~pathlib.Path` that was written.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format {fmt!r}. Choose from {SUPPORTED_FORMATS}."
        )

    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "text":
        content = format_text(diff)
    elif fmt == "json":
        content = format_json(diff)
    else:
        content = _diff_to_sql(diff)

    dest.write_text(content, encoding="utf-8")
    return dest
