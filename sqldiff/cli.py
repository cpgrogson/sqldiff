"""Command-line interface for sqldiff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqldiff.differ import diff_schemas
from sqldiff.loader import load_from_file, load_from_directory
from sqldiff.reporter import ReportOptions, Report
from sqldiff.exporter import export_diff, SUPPORTED_FORMATS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqldiff",
        description="Diff schema changes between two SQL snapshots.",
    )
    parser.add_argument("before", help="Path to the 'before' SQL file or directory.")
    parser.add_argument("after", help="Path to the 'after' SQL file or directory.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable coloured output.",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 when differences are found.",
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        default=None,
        help="Write the diff to FILE in addition to stdout.",
    )
    parser.add_argument(
        "--export-format",
        choices=list(SUPPORTED_FORMATS),
        default="text",
        help="Format used when --export is specified (default: text).",
    )
    return parser


def _load(path: str):
    p = Path(path)
    if p.is_dir():
        return load_from_directory(path)
    return load_from_file(path)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        before = _load(args.before)
        after = _load(args.after)
    except (FileNotFoundError, ValueError) as exc:
        print(f"sqldiff: error: {exc}", file=sys.stderr)
        return 2

    diff = diff_schemas(before, after)

    options = ReportOptions(
        fmt=args.format,
        color=not args.no_color,
    )
    report = Report(diff=diff, options=options)
    print(report.render())

    if args.export:
        try:
            out_path = export_diff(diff, args.export, fmt=args.export_format)
            print(f"sqldiff: diff exported to {out_path}", file=sys.stderr)
        except ValueError as exc:
            print(f"sqldiff: export error: {exc}", file=sys.stderr)
            return 2

    if args.exit_code and diff.has_changes:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
