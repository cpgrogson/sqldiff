"""Generate migration scripts from schema diffs."""

from dataclasses import dataclass, field
from typing import List, Optional

from sqldiff.differ import SchemaDiff
from sqldiff.schema import Column, Table


@dataclass
class MigrationScript:
    """Holds the generated SQL migration statements."""

    up_statements: List[str] = field(default_factory=list)
    down_statements: List[str] = field(default_factory=list)

    def up(self) -> str:
        """Return the forward migration SQL."""
        return "\n".join(self.up_statements)

    def down(self) -> str:
        """Return the rollback migration SQL."""
        return "\n".join(self.down_statements)

    def is_empty(self) -> bool:
        return not self.up_statements and not self.down_statements


def _column_def(col: Column) -> str:
    parts = [col.name, col.col_type]
    if not col.nullable:
        parts.append("NOT NULL")
    if col.default is not None:
        parts.append(f"DEFAULT {col.default}")
    return " ".join(parts)


def _add_column_sql(table: str, col: Column) -> str:
    return f"ALTER TABLE {table} ADD COLUMN {_column_def(col)};"


def _drop_column_sql(table: str, col_name: str) -> str:
    return f"ALTER TABLE {table} DROP COLUMN {col_name};"


def _create_table_sql(table: Table) -> str:
    col_defs = ",\n  ".join(_column_def(c) for c in table.columns)
    return f"CREATE TABLE {table.name} (\n  {col_defs}\n);"


def _drop_table_sql(table_name: str) -> str:
    return f"DROP TABLE IF EXISTS {table_name};"


def generate_migration(diff: SchemaDiff) -> MigrationScript:
    """Produce up/down SQL migration statements from a SchemaDiff."""
    script = MigrationScript()

    for table in diff.tables_added:
        script.up_statements.append(_create_table_sql(table))
        script.down_statements.append(_drop_table_sql(table.name))

    for table in diff.tables_removed:
        script.up_statements.append(_drop_table_sql(table.name))
        script.down_statements.append(_create_table_sql(table))

    for table_diff in diff.tables_modified:
        tname = table_diff.table_name
        for col in table_diff.columns_added:
            script.up_statements.append(_add_column_sql(tname, col))
            script.down_statements.append(_drop_column_sql(tname, col.name))
        for col in table_diff.columns_removed:
            script.up_statements.append(_drop_column_sql(tname, col.name))
            script.down_statements.append(_add_column_sql(tname, col))

    return script
