"""CLI entry-point for the schema dependency grapher."""
from __future__ import annotations

import argparse
import sys

from sqldiff.loader import load_from_file, load_from_directory
from sqldiff.grapher import build_graph


def build_graph_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqldiff-graph",
        description="Show table dependency graph inferred from <table>_id columns.",
    )
    p.add_argument("source", help="SQL file or directory of SQL files")
    p.add_argument(
        "--order",
        action="store_true",
        default=False,
        help="Print tables in topological (dependency) order",
    )
    p.add_argument(
        "--roots",
        action="store_true",
        default=False,
        help="Print only root tables (no dependencies)",
    )
    p.add_argument(
        "--leaves",
        action="store_true",
        default=False,
        help="Print only leaf tables (nothing depends on them)",
    )
    return p


def _load(source: str):
    import os
    if os.path.isdir(source):
        return load_from_directory(source)
    return load_from_file(source)


def main(argv=None) -> int:
    parser = build_graph_parser()
    args = parser.parse_args(argv)

    try:
        schema = _load(args.source)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    graph = build_graph(schema)

    if args.order:
        tables = graph.tables_in_order()
    elif args.roots:
        tables = sorted(graph.roots())
    elif args.leaves:
        tables = sorted(graph.leaves())
    else:
        tables = sorted(graph.nodes)

    for table in tables:
        node = graph.nodes[table]
        deps = ", ".join(sorted(node.depends_on)) if node.depends_on else "-"
        print(f"{table:30s}  depends_on: {deps}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
