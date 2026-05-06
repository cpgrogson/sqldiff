"""Tests for sqldiff.reporter module."""

import json
import pytest
from sqldiff.reporter import build_report, Report, ReportOptions, _list_unchanged
from sqldiff.differ import SchemaDiff, TableDiff


def _empty_diff():
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables={})


def _diff_with_added():
    return SchemaDiff(added_tables=["users"], removed_tables=[], modified_tables={})


def test_build_report_defaults():
    diff = _empty_diff()
    report = build_report(diff)
    assert isinstance(report, Report)
    assert report.options.output_format == "text"
    assert report.options.title is None
    assert report.options.include_unchanged is False


def test_build_report_with_options():
    diff = _empty_diff()
    report = build_report(diff, output_format="json", title="My Report")
    assert report.options.output_format == "json"
    assert report.options.title == "My Report"


def test_render_text_no_changes():
    diff = _empty_diff()
    report = build_report(diff)
    output = report.render()
    assert isinstance(output, str)
    assert len(output) > 0


def test_render_text_with_title():
    diff = _diff_with_added()
    report = build_report(diff, title="Schema v2")
    output = report.render()
    assert "# Schema v2" in output


def test_render_json_structure():
    diff = _diff_with_added()
    report = build_report(diff, output_format="json")
    output = report.render()
    data = json.loads(output)
    assert "added_tables" in data
    assert "users" in data["added_tables"]


def test_render_json_with_title():
    diff = _empty_diff()
    report = build_report(diff, output_format="json", title="Test")
    data = json.loads(report.render())
    assert data["title"] == "Test"


def test_render_json_include_unchanged():
    diff = _empty_diff()
    report = build_report(diff, output_format="json", include_unchanged=True)
    data = json.loads(report.render())
    assert "unchanged_tables" in data


def test_render_text_include_unchanged_empty():
    diff = _empty_diff()
    report = build_report(diff, include_unchanged=True)
    output = report.render()
    # No unchanged tables to list when modified_tables is empty
    assert isinstance(output, str)


def test_list_unchanged_no_real_changes():
    td = TableDiff(added_columns=[], removed_columns=[], modified_columns={})
    diff = SchemaDiff(added_tables=[], removed_tables=[], modified_tables={"orders": td})
    result = _list_unchanged(diff)
    assert "orders" in result
