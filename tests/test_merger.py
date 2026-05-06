"""Tests for envpatch.merger module."""

import pytest
from envpatch.parser import EnvFile, EnvEntry
from envpatch.differ import diff, ChangeType
from envpatch.merger import merge, ConflictStrategy, MergeConflict, MergeResult


def make_env(*pairs) -> EnvFile:
    entries = [EnvEntry(key=k, value=v) for k, v in pairs]
    return EnvFile(entries=entries)


def test_merge_added_key():
    base = make_env(("A", "1"))
    target = make_env(("A", "1"), ("B", "2"))
    d = diff(base, target)
    result = merge(base, d)
    assert result.merged.get("B") == "2"
    assert result.merged.get("A") == "1"
    assert len(result.applied) == 1
    assert len(result.skipped) == 0


def test_merge_removed_key():
    base = make_env(("A", "1"), ("B", "2"))
    target = make_env(("A", "1"))
    d = diff(base, target)
    result = merge(base, d)
    assert result.merged.get("B") is None
    assert result.merged.get("A") == "1"


def test_merge_changed_key_theirs():
    base = make_env(("A", "old"))
    target = make_env(("A", "new"))
    d = diff(base, target)
    result = merge(base, d, strategy=ConflictStrategy.THEIRS)
    assert result.merged.get("A") == "new"
    assert len(result.conflicts) == 1
    assert result.conflicts[0].resolved_value == "new"


def test_merge_changed_key_ours():
    base = make_env(("A", "old"))
    target = make_env(("A", "new"))
    d = diff(base, target)
    result = merge(base, d, strategy=ConflictStrategy.OURS)
    assert result.merged.get("A") == "old"
    assert result.conflicts[0].resolved_value == "old"


def test_merge_prompt_strategy_leaves_unresolved():
    base = make_env(("A", "old"))
    target = make_env(("A", "new"))
    d = diff(base, target)
    result = merge(base, d, strategy=ConflictStrategy.PROMPT)
    assert result.has_conflicts is True
    assert result.conflicts[0].resolved_value is None
    assert len(result.skipped) == 1


def test_merge_conflict_manual_resolve():
    conflict = MergeConflict(key="X", base_value="a", incoming_value="b")
    conflict.resolve("b")
    assert conflict.resolved_value == "b"


def test_merge_added_key_no_conflict_when_not_existing():
    base = make_env(("A", "1"))
    target = make_env(("A", "1"), ("B", "2"))
    d = diff(base, target)
    result = merge(base, d, existing_keys_conflict=True)
    assert len(result.conflicts) == 0
    assert result.merged.get("B") == "2"


def test_merge_added_key_conflict_when_already_exists():
    base = make_env(("A", "1"), ("B", "old"))
    target = make_env(("A", "1"), ("B", "new"))
    # Manually craft a diff that marks B as ADDED to simulate conflict
    from envpatch.differ import DiffEntry, DiffResult, ChangeType
    d = DiffResult(changes=[DiffEntry(key="B", change_type=ChangeType.ADDED, old_value=None, new_value="new")])
    result = merge(base, d, strategy=ConflictStrategy.THEIRS, existing_keys_conflict=True)
    assert result.merged.get("B") == "new"
    assert len(result.conflicts) == 1


def test_merge_changed_key_missing_in_base_skipped():
    base = make_env(("A", "1"))
    from envpatch.differ import DiffEntry, DiffResult, ChangeType
    d = DiffResult(changes=[DiffEntry(key="GHOST", change_type=ChangeType.CHANGED, old_value="x", new_value="y")])
    result = merge(base, d)
    assert result.merged.get("GHOST") is None
    assert len(result.skipped) == 1


def test_merge_result_no_conflicts():
    base = make_env(("A", "1"))
    target = make_env(("A", "1"), ("B", "2"))
    d = diff(base, target)
    result = merge(base, d)
    assert result.has_conflicts is False
