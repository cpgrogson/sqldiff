"""Command-line interface for sqldiff."""

import argparse
import sys
from sqldiff.loader import load_from_file, load_from_directory
from sqldiff.differ import diff_schemas
from sqldiff.reporter import build_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqldiff",
        description="Diff schema changes between two SQL snapshots.",
    )
    parser.add_argument("old", help="Path to old schema file or directory")
    parser.add_argument("new", help="Path to new schema file or directory")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional report title",
    )
    parser.add_argument(
        "--include-unchanged",
        action="store_true",
        default=False,
        help="Include unchanged tables in output",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if differences are found",
    )
    return parser


def _load(path: str):
    import os
    if os.path.isdir(path):
        return load_from_directory(path)
    return load_from_file(path)


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        old_schema = _load(args.old)
        new_schema = _load(args.new)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    diff = diff_schemas(old_schema, new_schema)
    report = build_report(
        diff,
        output_format=args.output_format,
        title=args.title,
        include_unchanged=args.include_unchanged,
    )
    print(report.render())

    if args.exit_code and diff.has_changes():
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
