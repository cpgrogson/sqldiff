"""CLI entry-point for the schema column tracer."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqldiff.loader import load_from_file
from sqldiff.tracer import trace_schema, trace_column


def build_trace_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqldiff-trace",
        description="Trace column lineage across ordered schema snapshots.",
    )
    p.add_argument(
        "snapshots",
        nargs="+",
        metavar="LABEL:FILE",
        help="Ordered list of label:file pairs, e.g. v1:schema1.sql v2:schema2.sql",
    )
    p.add_argument("--table", metavar="TABLE", help="Restrict trace to a single table")
    p.add_argument("--column", metavar="COLUMN", help="Restrict trace to a single column (requires --table)")
    p.add_argument("--format", choices=["text", "json"], default="text")
    return p


def _parse_snapshot_arg(arg: str):
    if ":" not in arg:
        print(f"error: snapshot argument must be LABEL:FILE, got: {arg}", file=sys.stderr)
        sys.exit(1)
    label, path = arg.split(":", 1)
    if not Path(path).exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    schema = load_from_file(path)
    return {label: schema}


def main(argv=None) -> None:
    parser = build_trace_parser()
    args = parser.parse_args(argv)

    snapshots = [_parse_snapshot_arg(s) for s in args.snapshots]

    if args.column and not args.table:
        print("error: --column requires --table", file=sys.stderr)
        sys.exit(1)

    if args.table and args.column:
        report_lineages = [trace_column(snapshots, args.table, args.column)]
    elif args.table:
        full = trace_schema(snapshots)
        report_lineages = full.for_table(args.table)
    else:
        full = trace_schema(snapshots)
        report_lineages = full.lineages

    if args.format == "json":
        out = []
        for ln in report_lineages:
            out.append({
                "table": ln.table,
                "column": ln.column,
                "history": [
                    {k: v for k, v in e.items() if k != "column"}
                    for e in ln.history
                ],
            })
        print(json.dumps(out, indent=2))
    else:
        if not report_lineages:
            print("No lineage data found.")
        for ln in report_lineages:
            print(str(ln))
            for entry in ln.history:
                col_info = ""
                if entry.get("column"):
                    col_info = f" type={entry['column'].type}"
                print(f"    [{entry['snapshot']}] {entry['status']}{col_info}")
