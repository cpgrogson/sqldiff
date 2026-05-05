"""Data models representing database schema objects."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Column:
    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Column):
            return NotImplemented
        return (
            self.name == other.name
            and self.data_type == other.data_type
            and self.nullable == other.nullable
            and self.default == other.default
            and self.primary_key == other.primary_key
        )


@dataclass
class Index:
    name: str
    columns: List[str]
    unique: bool = False


@dataclass
class Table:
    name: str
    columns: Dict[str, Column] = field(default_factory=dict)
    indexes: Dict[str, Index] = field(default_factory=dict)

    def add_column(self, column: Column) -> None:
        self.columns[column.name] = column

    def add_index(self, index: Index) -> None:
        self.indexes[index.name] = index


@dataclass
class Schema:
    tables: Dict[str, Table] = field(default_factory=dict)

    def add_table(self, table: Table) -> None:
        self.tables[table.name] = table

    def get_table(self, name: str) -> Optional[Table]:
        return self.tables.get(name)
