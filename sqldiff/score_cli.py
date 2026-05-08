"""CLI entry-point: ``sqldiff-score`` — print a similarity score for two SQL files."""
from __future__ import annotations

import argparse
import sys

from sqldiff.loader import load_from_file
from sqldiff.differ import diff_schemas
from sqldiff.scorer import score_schemas


def build_score_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqldiff-score",
        description="Compute a similarity score between two SQL schema files.",
    )
    p.add_argument("old", help="Path to the old SQL schema file")
    p.add_argument("new", help="Path to the new SQL schema file")
    p.add_argument(
        "--threshold",
        type=float,
        default=None,
        metavar="T",
        help=(
            "Exit with code 1 when the similarity score drops below T "
            "(value between 0.0 and 1.0)."
        ),
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output; useful when only the exit code matters.",
    )
    return p


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    parser = build_score_parser()
    args = parser.parse_args(argv)

    try:
        old_schema = load_from_file(args.old)
        new_schema = load_from_file(args.new)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 2

    diff = diff_schemas(old_schema, new_schema)
    result = score_schemas(old_schema, new_schema, diff)

    if not args.quiet:
        print(str(result))

    if args.threshold is not None and result.score < args.threshold:
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
