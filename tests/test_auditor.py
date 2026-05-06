"""Tests for envpatch.auditor."""

import json
import os
import pytest

from envpatch.auditor import (
    AuditEntry,
    create_entry,
    append_to_log,
    load_log,
)


# ---------------------------------------------------------------------------
# create_entry
# ---------------------------------------------------------------------------

def test_create_entry_defaults():
    entry = create_entry(operation="diff", base_file=".env")
    assert entry.operation == "diff"
    assert entry.base_file == ".env"
    assert entry.other_file is None
    assert entry.keys_added == []
    assert entry.keys_removed == []
    assert entry.keys_changed == []
    assert entry.keys_conflicted == []
    assert entry.strategy is None
    assert entry.dry_run is False
    assert entry.timestamp  # non-empty


def test_create_entry_with_all_fields():
    entry = create_entry(
        operation="merge",
        base_file=".env",
        other_file=".env.prod",
        keys_added=["NEW_KEY"],
        keys_removed=["OLD_KEY"],
        keys_changed=["DB_HOST"],
        keys_conflicted=["SECRET"],
        strategy="theirs",
        dry_run=True,
    )
    assert entry.operation == "merge"
    assert entry.other_file == ".env.prod"
    assert entry.keys_added == ["NEW_KEY"]
    assert entry.keys_removed == ["OLD_KEY"]
    assert entry.keys_changed == ["DB_HOST"]
    assert entry.keys_conflicted == ["SECRET"]
    assert entry.strategy == "theirs"
    assert entry.dry_run is True


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_contains_operation_and_file():
    entry = create_entry(operation="patch", base_file=".env")
    summary = entry.summary()
    assert "PATCH" in summary
    assert ".env" in summary


def test_summary_includes_other_file():
    entry = create_entry(operation="merge", base_file=".env", other_file=".env.staging")
    assert ".env.staging" in entry.summary()


def test_summary_lists_changed_keys():
    entry = create_entry(operation="merge", base_file=".env", keys_changed=["FOO", "BAR"])
    summary = entry.summary()
    assert "changed" in summary
    assert "FOO" in summary
    assert "BAR" in summary


def test_summary_dry_run_flag():
    entry = create_entry(operation="patch", base_file=".env", dry_run=True)
    assert "dry-run" in entry.summary()


# ---------------------------------------------------------------------------
# append_to_log / load_log
# ---------------------------------------------------------------------------

def test_append_and_load_single_entry(tmp_path):
    log_file = str(tmp_path / "audit.log")
    entry = create_entry(operation="diff", base_file=".env")
    append_to_log(entry, log_file)
    loaded = load_log(log_file)
    assert len(loaded) == 1
    assert loaded[0].operation == "diff"
    assert loaded[0].base_file == ".env"


def test_append_multiple_entries(tmp_path):
    log_file = str(tmp_path / "audit.log")
    for op in ("diff", "merge", "patch"):
        append_to_log(create_entry(operation=op, base_file=".env"), log_file)
    loaded = load_log(log_file)
    assert len(loaded) == 3
    assert [e.operation for e in loaded] == ["diff", "merge", "patch"]


def test_load_log_missing_file(tmp_path):
    result = load_log(str(tmp_path / "nonexistent.log"))
    assert result == []


def test_log_is_valid_jsonl(tmp_path):
    log_file = str(tmp_path / "audit.log")
    entry = create_entry(operation="merge", base_file=".env", keys_added=["X"])
    append_to_log(entry, log_file)
    with open(log_file) as fh:
        data = json.loads(fh.readline())
    assert data["operation"] == "merge"
    assert data["keys_added"] == ["X"]
