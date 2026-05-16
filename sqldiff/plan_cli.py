"""CLI entry-point for the migration planner."""
from __future__ import annotations

import argparse
import json
import sys

from sqldiff.loader import load_from_file
from sqldiff.differ import diff_schemas
from sqldiff.planner import plan_migration


def build_plan_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqldiff-plan",
        description="Show an ordered migration plan between two SQL schema files.",
    )
    p.add_argument("old", help="Path to the old schema SQL file.")
    p.add_argument("new", help="Path to the new schema SQL file.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when there are migration steps.",
    )
    return p


def _load(path: str):
    try:
        return load_from_file(path)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


def main(argv=None) -> None:
    parser = build_plan_parser()
    args = parser.parse_args(argv)

    old_schema = _load(args.old)
    new_schema = _load(args.new)

    diff = diff_schemas(old_schema, new_schema)
    plan = plan_migration(diff)

    if args.format == "json":
        data = {
            "steps": [
                {"order": s.order, "action": s.action, "table": s.table, "detail": s.detail}
                for s in plan.steps
            ],
            "warnings": plan.warnings,
        }
        print(json.dumps(data, indent=2))
    else:
        print(str(plan))

    if args.exit_code and not plan.is_empty():
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
