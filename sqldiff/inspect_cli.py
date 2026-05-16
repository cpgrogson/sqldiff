"""CLI entry-point for the schema inspector."""
from __future__ import annotations

import argparse
import json
import sys

from sqldiff.inspector import inspect_schema
from sqldiff.loader import load_from_file, load_from_string


def build_inspect_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="sqldiff-inspect",
        description="Inspect a SQL schema file and print high-level statistics.",
    )
    if parent is not None:
        parser = parent.add_parser("inspect", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("file", help="Path to the SQL schema file to inspect.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="format",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--table",
        metavar="TABLE",
        default=None,
        help="Restrict output to a single table.",
    )
    return parser


def _load(path: str):
    try:
        return load_from_file(path)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    parser = build_inspect_parser()
    args = parser.parse_args(argv)

    schema = _load(args.file)
    inspection = inspect_schema(schema)

    if args.table:
        match = next((t for t in inspection.tables if t.name == args.table), None)
        if match is None:
            print(f"error: table '{args.table}' not found", file=sys.stderr)
            sys.exit(1)
        data = match.to_dict()
        if args.format == "json":
            print(json.dumps(data, indent=2))
        else:
            print(f"Table   : {match.name}")
            print(f"Columns : {match.column_count}")
            print(f"Indexes : {match.index_count}")
            print(f"Nullable: {', '.join(match.nullable_columns) or '—'}")
            print(f"Defaults: {', '.join(match.columns_with_defaults) or '—'}")
            print(f"Has PK  : {match.has_primary_key}")
        return

    if args.format == "json":
        print(json.dumps(inspection.to_dict(), indent=2))
    else:
        print(str(inspection))
