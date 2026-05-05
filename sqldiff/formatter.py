"""Format a SchemaDiff into human-readable or SQL output."""

from sqldiff.differ import SchemaDiff


def format_text(diff: SchemaDiff) -> str:
    """Return a plain-text summary of schema changes."""
    if not diff.has_changes:
        return "No schema changes detected."

    lines = []

    for table in diff.tables_added:
        lines.append(f"[+] TABLE  {table}")

    for table in diff.tables_removed:
        lines.append(f"[-] TABLE  {table}")

    for col in sorted(diff.columns_added):
        lines.append(f"[+] COLUMN {col}")

    for col in sorted(diff.columns_removed):
        lines.append(f"[-] COLUMN {col}")

    for col in sorted(diff.columns_modified):
        lines.append(f"[~] COLUMN {col}")

    return "\n".join(lines)


def format_json(diff: SchemaDiff) -> dict:
    """Return a dict representation of the diff suitable for JSON serialisation."""
    return {
        "tables": {
            "added": diff.tables_added,
            "removed": diff.tables_removed,
        },
        "columns": {
            "added": sorted(diff.columns_added),
            "removed": sorted(diff.columns_removed),
            "modified": sorted(diff.columns_modified),
        },
        "has_changes": diff.has_changes,
    }
