"""Tests for sqldiff.tagger."""
import pytest

from sqldiff.tagger import (
    TagSet,
    TaggedDiff,
    tag_diff,
    filter_by_tag,
    collect_tags,
)
from sqldiff.differ import SchemaDiff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_diff(**kwargs) -> SchemaDiff:
    return SchemaDiff(
        added_tables=kwargs.get('added_tables', []),
        removed_tables=kwargs.get('removed_tables', []),
        modified_tables=kwargs.get('modified_tables', []),
    )


# ---------------------------------------------------------------------------
# TagSet
# ---------------------------------------------------------------------------

def test_tagset_normalises_case():
    ts = TagSet(['Alpha', 'BETA', 'gamma'])
    assert 'alpha' in ts
    assert 'beta' in ts
    assert 'gamma' in ts


def test_tagset_strips_whitespace():
    ts = TagSet(['  foo  ', 'bar'])
    assert 'foo' in ts


def test_tagset_ignores_blank_entries():
    ts = TagSet(['', '   ', 'real'])
    assert len(ts) == 1


def test_tagset_str_sorted():
    ts = TagSet(['zebra', 'apple'])
    assert str(ts) == 'apple, zebra'


def test_tagset_str_empty():
    ts = TagSet()
    assert str(ts) == '(none)'


def test_tagset_union():
    a = TagSet(['x', 'y'])
    b = TagSet(['y', 'z'])
    u = a.union(b)
    assert 'x' in u
    assert 'y' in u
    assert 'z' in u


def test_tagset_intersection():
    a = TagSet(['x', 'y'])
    b = TagSet(['y', 'z'])
    i = a.intersection(b)
    assert 'y' in i
    assert 'x' not in i


def test_tagset_is_empty():
    assert TagSet().is_empty()
    assert not TagSet(['t']).is_empty()


# ---------------------------------------------------------------------------
# tag_diff / TaggedDiff
# ---------------------------------------------------------------------------

def test_tag_diff_returns_tagged_diff():
    diff = _empty_diff()
    td = tag_diff(diff, ['release', 'v2'])
    assert isinstance(td, TaggedDiff)
    assert td.has_tag('release')
    assert td.has_tag('v2')
    assert not td.has_tag('hotfix')


def test_tag_diff_empty_tags():
    td = tag_diff(_empty_diff(), [])
    assert td.tags.is_empty()


# ---------------------------------------------------------------------------
# filter_by_tag
# ---------------------------------------------------------------------------

def test_filter_by_tag_returns_matching():
    td1 = tag_diff(_empty_diff(), ['alpha'])
    td2 = tag_diff(_empty_diff(), ['beta'])
    td3 = tag_diff(_empty_diff(), ['alpha', 'beta'])
    result = filter_by_tag([td1, td2, td3], 'alpha')
    assert td1 in result
    assert td2 not in result
    assert td3 in result


def test_filter_by_tag_no_matches():
    td = tag_diff(_empty_diff(), ['x'])
    assert filter_by_tag([td], 'y') == []


# ---------------------------------------------------------------------------
# collect_tags
# ---------------------------------------------------------------------------

def test_collect_tags_union_of_all():
    td1 = tag_diff(_empty_diff(), ['a', 'b'])
    td2 = tag_diff(_empty_diff(), ['b', 'c'])
    all_tags = collect_tags([td1, td2])
    assert 'a' in all_tags
    assert 'b' in all_tags
    assert 'c' in all_tags


def test_collect_tags_empty_list():
    result = collect_tags([])
    assert result.is_empty()
