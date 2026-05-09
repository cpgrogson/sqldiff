"""CLI entry-point for tagging and querying tagged diffs."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from sqldiff.loader import load_from_file
from sqldiff.differ import diff_schemas
from sqldiff.tagger import tag_diff, filter_by_tag, collect_tags, TaggedDiff


def build_tag_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='sqldiff-tag',
        description='Tag a schema diff and query tagged results.',
    )
    sub = p.add_subparsers(dest='command', required=True)

    # --- tag sub-command ---
    tag_cmd = sub.add_parser('tag', help='Diff two schemas and assign tags.')
    tag_cmd.add_argument('old', help='Path to the old SQL schema file.')
    tag_cmd.add_argument('new', help='Path to the new SQL schema file.')
    tag_cmd.add_argument('--tags', nargs='+', default=[], metavar='TAG',
                         help='One or more tags to attach to this diff.')
    tag_cmd.add_argument('--format', choices=['text', 'json'], default='text')

    # --- list sub-command ---
    list_cmd = sub.add_parser('list', help='List all unique tags across stored diffs.')
    list_cmd.add_argument('--format', choices=['text', 'json'], default='text')

    return p


# In-process store for demonstration purposes (reset per process).
_STORE: List[TaggedDiff] = []


def main(argv: List[str] | None = None) -> int:  # pragma: no cover – thin wrapper
    parser = build_tag_parser()
    args = parser.parse_args(argv)

    if args.command == 'tag':
        try:
            old_schema = load_from_file(args.old)
            new_schema = load_from_file(args.new)
        except (FileNotFoundError, TypeError) as exc:
            print(f'error: {exc}', file=sys.stderr)
            return 2

        diff = diff_schemas(old_schema, new_schema)
        td = tag_diff(diff, args.tags)
        _STORE.append(td)

        if args.format == 'json':
            payload = {
                'tags': list(td.tags),
                'has_changes': diff.has_changes,
                'added_tables': [t.name for t in diff.added_tables],
                'removed_tables': [t.name for t in diff.removed_tables],
            }
            print(json.dumps(payload, indent=2))
        else:
            status = 'changes detected' if diff.has_changes else 'no changes'
            print(f'[{status}]  tags: {td.tags}')
        return 1 if diff.has_changes else 0

    if args.command == 'list':
        all_tags = collect_tags(_STORE)
        if args.format == 'json':
            print(json.dumps({'tags': list(all_tags)}))
        else:
            print('Tags:', str(all_tags))
        return 0

    return 0


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())
