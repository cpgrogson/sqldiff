"""Tag schemas and diffs with user-defined labels for organisation and filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List

from sqldiff.schema import Schema
from sqldiff.differ import SchemaDiff


@dataclass
class TagSet:
    """An immutable collection of string tags."""
    _tags: FrozenSet[str] = field(default_factory=frozenset)

    def __init__(self, tags: Iterable[str] = ()) -> None:
        object.__setattr__(self, '_tags', frozenset(t.strip().lower() for t in tags if t.strip()))

    def __contains__(self, tag: str) -> bool:
        return tag.strip().lower() in self._tags

    def __iter__(self):
        return iter(sorted(self._tags))

    def __len__(self) -> int:
        return len(self._tags)

    def __str__(self) -> str:
        return ', '.join(sorted(self._tags)) if self._tags else '(none)'

    def union(self, other: 'TagSet') -> 'TagSet':
        return TagSet(self._tags | other._tags)

    def intersection(self, other: 'TagSet') -> 'TagSet':
        return TagSet(self._tags & other._tags)

    def is_empty(self) -> bool:
        return len(self._tags) == 0


@dataclass
class TaggedDiff:
    """A SchemaDiff decorated with a TagSet."""
    diff: SchemaDiff
    tags: TagSet = field(default_factory=TagSet)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


def tag_diff(diff: SchemaDiff, tags: Iterable[str]) -> TaggedDiff:
    """Wrap *diff* with the supplied *tags*."""
    return TaggedDiff(diff=diff, tags=TagSet(tags))


def filter_by_tag(diffs: List[TaggedDiff], tag: str) -> List[TaggedDiff]:
    """Return only those TaggedDiffs that carry *tag*."""
    return [d for d in diffs if d.has_tag(tag)]


def collect_tags(diffs: Iterable[TaggedDiff]) -> TagSet:
    """Return the union of all tags across *diffs*."""
    result: FrozenSet[str] = frozenset()
    for d in diffs:
        result = result | frozenset(d.tags)
    return TagSet(result)
