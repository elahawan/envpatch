"""Tests for envpatch.differ_summary."""

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.differ import diff_env_files
from envpatch.differ_summary import DiffSummary, summarize_diff, format_summary


def make_env(*pairs) -> EnvFile:
    entries = [EnvEntry(key=k, value=v) for k, v in pairs]
    return EnvFile(entries=entries)


# --- summarize_diff ---

def test_identical_files_are_identical():
    env = make_env(("A", "1"), ("B", "2"))
    summary = summarize_diff(diff_env_files(env, env))
    assert summary.is_identical
    assert summary.total_changes == 0


def test_added_key_counted():
    base = make_env(("A", "1"))
    other = make_env(("A", "1"), ("B", "2"))
    summary = summarize_diff(diff_env_files(base, other))
    assert summary.added_count == 1
    assert "B" in summary.added_keys
    assert summary.removed_count == 0
    assert summary.changed_count == 0


def test_removed_key_counted():
    base = make_env(("A", "1"), ("B", "2"))
    other = make_env(("A", "1"))
    summary = summarize_diff(diff_env_files(base, other))
    assert summary.removed_count == 1
    assert "B" in summary.removed_keys


def test_changed_key_counted():
    base = make_env(("A", "1"))
    other = make_env(("A", "99"))
    summary = summarize_diff(diff_env_files(base, other))
    assert summary.changed_count == 1
    assert "A" in summary.changed_keys


def test_unchanged_key_counted():
    base = make_env(("A", "1"), ("B", "2"))
    other = make_env(("A", "1"), ("B", "99"))
    summary = summarize_diff(diff_env_files(base, other))
    assert summary.unchanged_count == 1


def test_total_changes_sums_add_remove_change():
    base = make_env(("A", "1"), ("B", "2"))
    other = make_env(("A", "99"), ("C", "3"))
    summary = summarize_diff(diff_env_files(base, other))
    assert summary.total_changes == summary.added_count + summary.removed_count + summary.changed_count


def test_added_keys_are_sorted():
    base = make_env()
    other = make_env(("Z", "1"), ("A", "2"), ("M", "3"))
    summary = summarize_diff(diff_env_files(base, other))
    assert summary.added_keys == sorted(summary.added_keys)


def test_as_dict_contains_expected_keys():
    env = make_env(("X", "1"))
    summary = summarize_diff(diff_env_files(env, env))
    d = summary.as_dict()
    for key in ("added", "removed", "changed", "unchanged", "total_changes",
                "added_keys", "removed_keys", "changed_keys"):
        assert key in d


# --- format_summary ---

def test_format_identical_no_color():
    env = make_env(("A", "1"))
    summary = summarize_diff(diff_env_files(env, env))
    out = format_summary(summary, color=False)
    assert "identical" in out.lower()


def test_format_shows_added_key():
    base = make_env()
    other = make_env(("NEW_KEY", "val"))
    summary = summarize_diff(diff_env_files(base, other))
    out = format_summary(summary, color=False)
    assert "NEW_KEY" in out
    assert "added" in out


def test_format_shows_removed_key():
    base = make_env(("OLD_KEY", "val"))
    other = make_env()
    summary = summarize_diff(diff_env_files(base, other))
    out = format_summary(summary, color=False)
    assert "OLD_KEY" in out
    assert "removed" in out


def test_format_with_color_contains_ansi():
    base = make_env()
    other = make_env(("X", "1"))
    summary = summarize_diff(diff_env_files(base, other))
    out = format_summary(summary, color=True)
    assert "\033[" in out
