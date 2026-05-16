"""Schema inspector: surface high-level facts about a Schema for reporting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from sqldiff.schema import Schema, Table


@dataclass
class TableInspection:
    name: str
    column_count: int
    index_count: int
    nullable_columns: List[str] = field(default_factory=list)
    columns_with_defaults: List[str] = field(default_factory=list)
    has_primary_key: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "column_count": self.column_count,
            "index_count": self.index_count,
            "nullable_columns": self.nullable_columns,
            "columns_with_defaults": self.columns_with_defaults,
            "has_primary_key": self.has_primary_key,
        }


@dataclass
class SchemaInspection:
    table_count: int
    total_columns: int
    total_indexes: int
    tables: List[TableInspection] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "table_count": self.table_count,
            "total_columns": self.total_columns,
            "total_indexes": self.total_indexes,
            "tables": [t.to_dict() for t in self.tables],
        }

    def __str__(self) -> str:  # pragma: no cover
        lines = [
            f"Tables : {self.table_count}",
            f"Columns: {self.total_columns}",
            f"Indexes: {self.total_indexes}",
        ]
        for t in self.tables:
            pk = " [PK]" if t.has_primary_key else ""
            lines.append(f"  {t.name}{pk}: {t.column_count} cols, {t.index_count} idx")
        return "\n".join(lines)


def _inspect_table(table: Table) -> TableInspection:
    nullable = [c.name for c in table.columns if c.nullable]
    with_defaults = [c.name for c in table.columns if c.default is not None]
    has_pk = any(
        idx.name.lower() in ("primary", "primary key") or idx.unique
        for idx in table.indexes
    )
    return TableInspection(
        name=table.name,
        column_count=len(table.columns),
        index_count=len(table.indexes),
        nullable_columns=nullable,
        columns_with_defaults=with_defaults,
        has_primary_key=has_pk,
    )


def inspect_schema(schema: Schema) -> SchemaInspection:
    """Return a :class:`SchemaInspection` summarising *schema*."""
    table_inspections = [_inspect_table(t) for t in schema.tables.values()]
    return SchemaInspection(
        table_count=len(table_inspections),
        total_columns=sum(t.column_count for t in table_inspections),
        total_indexes=sum(t.index_count for t in table_inspections),
        tables=table_inspections,
    )
