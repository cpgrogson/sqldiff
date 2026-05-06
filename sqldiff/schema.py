"""Schema data model for sqldiff."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Column:
    name: str
    col_type: str
    nullable: bool = True
    default: Optional[str] = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Column):
            return NotImplemented
        return (
            self.name == other.name
            and self.col_type == other.col_type
            and self.nullable == other.nullable
            and self.default == other.default
        )


@dataclass
class Index:
    name: str
    columns: List[str]
    unique: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Index):
            return NotImplemented
        return (
            self.name == other.name
            and self.columns == other.columns
            and self.unique == other.unique
        )


@dataclass
class Table:
    name: str
    columns: List[Column] = field(default_factory=list)
    indexes: List[Index] = field(default_factory=list)

    def add_column(self, col: Column) -> None:
        self.columns.append(col)

    def remove_column(self, name: str) -> None:
        self.columns = [c for c in self.columns if c.name != name]

    def get_column(self, name: str) -> Optional[Column]:
        return next((c for c in self.columns if c.name == name), None)

    def add_index(self, idx: Index) -> None:
        self.indexes.append(idx)

    def get_index(self, name: str) -> Optional[Index]:
        return next((i for i in self.indexes if i.name == name), None)


@dataclass
class Schema:
    tables: Dict[str, Table] = field(default_factory=dict)

    def get_table(self, name: str) -> Optional[Table]:
        return self.tables.get(name)

    def table_names(self) -> List[str]:
        return list(self.tables.keys())
