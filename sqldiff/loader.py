"""Load schemas from SQL files or strings."""

from pathlib import Path
from typing import Union
from .parser import parse_sql
from .schema import Schema


def load_from_file(path: Union[str, Path]) -> Schema:
    """Read a SQL file and parse it into a Schema."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    sql = path.read_text(encoding="utf-8")
    return parse_sql(sql)


def load_from_string(sql: str) -> Schema:
    """Parse a SQL string into a Schema."""
    if not isinstance(sql, str):
        raise TypeError(f"Expected str, got {type(sql).__name__}")
    return parse_sql(sql)


def load_from_directory(directory: Union[str, Path], pattern: str = "*.sql") -> Schema:
    """Merge all matching SQL files in a directory into a single Schema."""
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")
    merged_tables = {}
    for sql_file in sorted(directory.glob(pattern)):
        schema = load_from_file(sql_file)
        merged_tables.update(schema.tables)
    from .schema import Schema
    return Schema(tables=merged_tables)
