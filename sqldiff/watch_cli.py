"""CLI entry-point for the schema watch sub-command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqldiff.differ import SchemaDiff
from sqldiff.formatter import format_text, format_json
from sqldiff.watcher import SchemaWatcher


def _make_callback(fmt: str, quiet: bool) -> object:
    """Return an on_change callback that prints diffs in *fmt* format."""

    def _callback(path: Path, diff: SchemaDiff) -> None:
        if quiet and not diff.has_changes:
            return
        header = f"[sqldiff] Change detected in {path}"
        print(header, file=sys.stderr)
        if fmt == "json":
            print(format_json(diff))
        else:
            print(format_text(diff))

    return _callback


def build_watch_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqldiff watch",
        description="Watch SQL schema files and print diffs on change.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help="SQL files to watch")
    p.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECS",
        help="Poll interval in seconds (default: 2.0)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output when there are no changes",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_watch_parser()
    args = parser.parse_args(argv)

    missing = [f for f in args.files if not Path(f).exists()]
    if missing:
        for m in missing:
            print(f"sqldiff watch: file not found: {m}", file=sys.stderr)
        sys.exit(2)

    callback = _make_callback(fmt=args.fmt, quiet=args.quiet)
    watcher = SchemaWatcher(
        paths=args.files,
        on_change=callback,
        interval=args.interval,
    )
    print(
        f"[sqldiff] Watching {len(args.files)} file(s). Press Ctrl+C to stop.",
        file=sys.stderr,
    )
    watcher.watch()


if __name__ == "__main__":  # pragma: no cover
    main()
