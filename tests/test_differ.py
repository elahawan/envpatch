"""Tests for envpatch.differ module."""

import pytest

from envpatch.differ import ChangeType, diff
from envpatch.parser import EnvFile


def make_env(text: str) -> EnvFile:
    return EnvFile.parse(text)


def test_diff_identical_files():
    base = make_env("FOO=bar\nBAZ=qux\n")
    target = make_env("FOO=bar\nBAZ=qux\n")
    result = diff(base, target)
    assert all(e.change_type == ChangeType.UNCHANGED for e in result.entries)
    assert not result.has_conflicts


def test_diff_added_key():
    base = make_env("FOO=bar\n")
    target = make_env("FOO=bar\nNEW_KEY=hello\n")
    result = diff(base, target)
    added = result.added
    assert len(added) == 1
    assert added[0].key == "NEW_KEY"
    assert added[0].new_value == "hello"
    assert added[0].old_value is None


def test_diff_removed_key():
    base = make_env("FOO=bar\nOLD=gone\n")
    target = make_env("FOO=bar\n")
    result = diff(base, target)
    removed = result.removed
    assert len(removed) == 1
    assert removed[0].key == "OLD"
    assert removed[0].old_value == "gone"
    assert removed[0].new_value is None


def test_diff_changed_key():
    base = make_env("FOO=old_value\n")
    target = make_env("FOO=new_value\n")
    result = diff(base, target)
    changed = result.changed
    assert len(changed) == 1
    assert changed[0].key == "FOO"
    assert changed[0].old_value == "old_value"
    assert changed[0].new_value == "new_value"


def test_diff_has_conflicts_when_changed():
    base = make_env("FOO=1\n")
    target = make_env("FOO=2\n")
    result = diff(base, target)
    assert result.has_conflicts


def test_diff_has_conflicts_when_removed():
    base = make_env("FOO=1\nBAR=2\n")
    target = make_env("FOO=1\n")
    result = diff(base, target)
    assert result.has_conflicts


def test_diff_no_conflicts_only_added():
    base = make_env("FOO=1\n")
    target = make_env("FOO=1\nBAR=2\n")
    result = diff(base, target)
    assert not result.has_conflicts


def test_diff_summary_contains_symbols():
    base = make_env("FOO=old\nBAR=same\nDEL=gone\n")
    target = make_env("FOO=new\nBAR=same\nADD=fresh\n")
    result = diff(base, target)
    summary = result.summary()
    assert "~" in summary
    assert "+" in summary
    assert "-" in summary
    assert "  " in summary


def test_diff_entry_repr_added():
    base = make_env("")
    target = make_env("X=1\n")
    result = diff(base, target)
    assert repr(result.added[0]) == "+ X=1"


def test_diff_entry_repr_removed():
    base = make_env("X=1\n")
    target = make_env("")
    result = diff(base, target)
    assert repr(result.removed[0]) == "- X=1"
