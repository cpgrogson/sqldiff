"""CLI entry-point for the schema profiler."""
from __future__ import annotations

import argparse
import json
import sys

from sqldiff.loader import load_from_file, load_from_string
from sqldiff.profiler import profile_schema


def build_profile_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqldiff-profile",
        description="Print statistics about a SQL schema file.",
    )
    parser.add_argument("schema", help="Path to the SQL schema file (or '-' for stdin)")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--table",
        metavar="TABLE",
        default=None,
        help="Restrict output to a single table",
    )
    return parser


def _load(path: str):
    if path == "-":
        return load_from_string(sys.stdin.read())
    return load_from_file(path)


def main(argv=None) -> int:
    parser = build_profile_parser()
    args = parser.parse_args(argv)

    try:
        schema = _load(args.schema)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    profile = profile_schema(schema)

    if args.table:
        matched = [tp for tp in profile.tables if tp.name == args.table]
        if not matched:
            print(f"error: table '{args.table}' not found in schema", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(matched[0].to_dict(), indent=2))
        else:
            tp = matched[0]
            print(f"Table   : {tp.name}")
            print(f"Columns : {tp.column_count}")
            print(f"Indexes : {tp.index_count}")
            if tp.nullable_columns:
                print(f"Nullable: {', '.join(tp.nullable_columns)}")
            if tp.columns_with_defaults:
                print(f"Defaults: {', '.join(tp.columns_with_defaults)}")
        return 0

    if args.format == "json":
        print(json.dumps(profile.to_dict(), indent=2))
    else:
        print(str(profile))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
