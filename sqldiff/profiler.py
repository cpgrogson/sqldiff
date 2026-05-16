"""Schema profiler: collects statistics and distribution info about a schema."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from sqldiff.schema import Schema, Table


@dataclass
class TableProfile:
    name: str
    column_count: int
    index_count: int
    nullable_columns: List[str] = field(default_factory=list)
    columns_with_defaults: List[str] = field(default_factory=list)
    column_types: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "column_count": self.column_count,
            "index_count": self.index_count,
            "nullable_columns": self.nullable_columns,
            "columns_with_defaults": self.columns_with_defaults,
            "column_types": self.column_types,
        }


@dataclass
class SchemaProfile:
    table_count: int
    total_columns: int
    total_indexes: int
    tables: List[TableProfile] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "table_count": self.table_count,
            "total_columns": self.total_columns,
            "total_indexes": self.total_indexes,
            "tables": [t.to_dict() for t in self.tables],
        }

    def __str__(self) -> str:
        lines = [
            f"Tables : {self.table_count}",
            f"Columns: {self.total_columns}",
            f"Indexes: {self.total_indexes}",
        ]
        for tp in self.tables:
            lines.append(f"  {tp.name}: {tp.column_count} cols, {tp.index_count} idx")
        return "\n".join(lines)


def _profile_table(table: Table) -> TableProfile:
    nullable = [c.name for c in table.columns if c.nullable]
    with_defaults = [c.name for c in table.columns if c.default is not None]
    type_counts: Dict[str, int] = {}
    for col in table.columns:
        norm = col.col_type.upper()
        type_counts[norm] = type_counts.get(norm, 0) + 1
    return TableProfile(
        name=table.name,
        column_count=len(table.columns),
        index_count=len(table.indexes),
        nullable_columns=nullable,
        columns_with_defaults=with_defaults,
        column_types=type_counts,
    )


def profile_schema(schema: Schema) -> SchemaProfile:
    """Return a :class:`SchemaProfile` describing *schema*."""
    table_profiles = [_profile_table(t) for t in schema.tables.values()]
    return SchemaProfile(
        table_count=len(table_profiles),
        total_columns=sum(tp.column_count for tp in table_profiles),
        total_indexes=sum(tp.index_count for tp in table_profiles),
        tables=table_profiles,
    )
