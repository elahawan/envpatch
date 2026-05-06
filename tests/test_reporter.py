"""Tests for envpatch.reporter module."""

import io

import pytest

from envpatch.differ import DiffEntry, DiffResult, ChangeType
from envpatch.reporter import format_diff_report, print_diff_report


def make_result(
    added=None, removed=None, changed=None, unchanged=None
) -> DiffResult:
    return DiffResult(
        added=added or [],
        removed=removed or [],
        changed=changed or [],
        unchanged=unchanged or [],
    )


def test_identical_files_report():
    result = make_result(unchanged=[DiffEntry(ChangeType.UNCHANGED, "KEY", "val", "val")])
    report = format_diff_report(result, use_color=False)
    assert "No differences found" in report


def test_added_key_report():
    entry = DiffEntry(ChangeType.ADDED, "NEW_KEY", None, "newval")
    result = make_result(added=[entry])
    report = format_diff_report(result, use_color=False)
    assert "+ NEW_KEY=newval" in report
    assert "1 added" in report


def test_removed_key_report():
    entry = DiffEntry(ChangeType.REMOVED, "OLD_KEY", "oldval", None)
    result = make_result(removed=[entry])
    report = format_diff_report(result, use_color=False)
    assert "- OLD_KEY=oldval" in report
    assert "1 removed" in report


def test_changed_key_report():
    entry = DiffEntry(ChangeType.CHANGED, "MY_KEY", "old", "new")
    result = make_result(changed=[entry])
    report = format_diff_report(result, use_color=False)
    assert "- MY_KEY=old" in report
    assert "+ MY_KEY=new" in report
    assert "1 changed" in report


def test_summary_multiple_types():
    result = make_result(
        added=[DiffEntry(ChangeType.ADDED, "A", None, "1")],
        removed=[DiffEntry(ChangeType.REMOVED, "B", "2", None)],
        changed=[DiffEntry(ChangeType.CHANGED, "C", "3", "4")],
    )
    report = format_diff_report(result, use_color=False)
    assert "1 added" in report
    assert "1 removed" in report
    assert "1 changed" in report


def test_color_codes_present_when_enabled():
    entry = DiffEntry(ChangeType.ADDED, "KEY", None, "val")
    result = make_result(added=[entry])
    report = format_diff_report(result, use_color=True)
    assert "\033[" in report


def test_color_codes_absent_when_disabled():
    entry = DiffEntry(ChangeType.ADDED, "KEY", None, "val")
    result = make_result(added=[entry])
    report = format_diff_report(result, use_color=False)
    assert "\033[" not in report


def test_print_diff_report_writes_to_stream():
    entry = DiffEntry(ChangeType.REMOVED, "X", "y", None)
    result = make_result(removed=[entry])
    stream = io.StringIO()
    print_diff_report(result, stream=stream, use_color=False)
    output = stream.getvalue()
    assert "- X=y" in output
