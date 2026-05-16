"""CLI entry-point for the 'sqldiff stat' command."""
from __future__ import annotations

import argparse
import json
import sys

from sqldiff.loader import load_from_file
from sqldiff.differ import diff_schemas
from sqldiff.differ_stats import build_stat_report


def build_stat_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="sqldiff-stat",
        description="Show aggregated statistics for a schema diff.",
    )
    parser.add_argument("before", help="Path to the 'before' SQL schema file")
    parser.add_argument("after", help="Path to the 'after' SQL schema file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if there are any changes",
    )
    return parser


def _load(path: str):
    try:
        return load_from_file(path)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(2)


def main(argv=None) -> None:
    parser = build_stat_parser()
    args = parser.parse_args(argv)

    before = _load(args.before)
    after = _load(args.after)

    diff = diff_schemas(before, after)
    report = build_stat_report(diff)

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(str(report))

    if args.exit_code and report.total_changes > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
