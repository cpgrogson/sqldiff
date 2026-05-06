"""Parse SQL CREATE TABLE statements into schema objects."""

import re
from typing import Dict
from .schema import Column, Index, Table, Schema


_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?(\w+)[`\"]?\s*\((.+)\)\s*;?",
    re.IGNORECASE | re.DOTALL,
)
_COLUMN_RE = re.compile(
    r"^[`\"]?(\w+)[`\"]?\s+(\w+(?:\(\d+(?:,\d+)?\))?)\s*(.*)",
    re.IGNORECASE,
)
_INDEX_RE = re.compile(
    r"(?:(UNIQUE)\s+)?INDEX\s+[`\"]?(\w+)[`\"]?\s*\(([^)]+)\)",
    re.IGNORECASE,
)


def _parse_column(line: str) -> Column | None:
    line = line.strip()
    m = _COLUMN_RE.match(line)
    if not m:
        return None
    name, col_type, rest = m.group(1), m.group(2), m.group(3)
    nullable = "NOT NULL" not in rest.upper()
    default = None
    default_m = re.search(r"DEFAULT\s+(\S+)", rest, re.IGNORECASE)
    if default_m:
        default = default_m.group(1).strip("'\"")
    return Column(name=name, col_type=col_type.upper(), nullable=nullable, default=default)


def _parse_index(line: str, table_name: str) -> Index | None:
    m = _INDEX_RE.search(line)
    if not m:
        return None
    unique = m.group(1) is not None
    index_name = m.group(2)
    columns = [c.strip().strip("`\"'") for c in m.group(3).split(",")]
    return Index(name=index_name, columns=columns, unique=unique)


def parse_sql(sql: str) -> "Schema":
    """Parse a SQL string containing CREATE TABLE statements into a Schema."""
    tables: Dict[str, Table] = {}
    for match in _CREATE_TABLE_RE.finditer(sql):
        table_name = match.group(1)
        body = match.group(2)
        columns: list[Column] = []
        indexes: list[Index] = []
        for raw_line in body.split(","):
            line = raw_line.strip()
            if not line:
                continue
            upper = line.upper().lstrip()
            if upper.startswith("INDEX") or upper.startswith("UNIQUE INDEX") or upper.startswith("KEY") or upper.startswith("UNIQUE KEY"):
                idx = _parse_index(line, table_name)
                if idx:
                    indexes.append(idx)
            elif upper.startswith("PRIMARY") or upper.startswith("CONSTRAINT") or upper.startswith("FOREIGN"):
                continue
            else:
                col = _parse_column(line)
                if col:
                    columns.append(col)
        tables[table_name] = Table(name=table_name, columns=columns, indexes=indexes)
    return Schema(tables=tables)
