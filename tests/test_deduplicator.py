"""Tests for envpatch.deduplicator."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.deduplicator import deduplicate_env_file, DeduplicateResult


def kv(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}")


def comment(text: str) -> EnvEntry:
    return EnvEntry(key=None, value=None, raw=f"# {text}")


def blank() -> EnvEntry:
    return EnvEntry(key=None, value=None, raw="")


def make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_no_duplicates_unchanged():
    env = make_env(kv("A", "1"), kv("B", "2"))
    result = deduplicate_env_file(env)
    assert not result.was_modified
    assert result.duplicate_count == 0
    assert len(result.entries) == 2


def test_single_duplicate_removed_keep_last():
    env = make_env(kv("A", "1"), kv("B", "2"), kv("A", "99"))
    result = deduplicate_env_file(env, keep="last")
    assert result.was_modified
    assert result.duplicate_count == 1
    keys = [e.key for e in result.entries if e.key]
    assert keys == ["B", "A"]
    a_entry = next(e for e in result.entries if e.key == "A")
    assert a_entry.value == "99"


def test_single_duplicate_removed_keep_first():
    env = make_env(kv("A", "1"), kv("B", "2"), kv("A", "99"))
    result = deduplicate_env_file(env, keep="first")
    assert result.was_modified
    assert result.duplicate_count == 1
    a_entry = next(e for e in result.entries if e.key == "A")
    assert a_entry.value == "1"


def test_multiple_duplicates_counted():
    env = make_env(kv("X", "a"), kv("X", "b"), kv("X", "c"))
    result = deduplicate_env_file(env, keep="last")
    assert result.duplicate_count == 2
    assert len([e for e in result.entries if e.key == "X"]) == 1


def test_comments_and_blanks_preserved():
    env = make_env(comment("header"), blank(), kv("A", "1"), kv("A", "2"))
    result = deduplicate_env_file(env, keep="first")
    assert result.entries[0].raw == "# header"
    assert result.entries[1].raw == ""
    assert len([e for e in result.entries if e.key == "A"]) == 1


def test_as_env_file_returns_env_file():
    env = make_env(kv("A", "1"), kv("A", "2"))
    result = deduplicate_env_file(env)
    env_file = result.as_env_file()
    assert hasattr(env_file, "entries")
    assert len(env_file.entries) == 1


def test_invalid_keep_raises():
    env = make_env(kv("A", "1"))
    with pytest.raises(ValueError, match="keep must be"):
        deduplicate_env_file(env, keep="middle")


def test_duplicates_dict_contains_correct_key():
    env = make_env(kv("FOO", "x"), kv("BAR", "y"), kv("FOO", "z"))
    result = deduplicate_env_file(env, keep="first")
    assert "FOO" in result.duplicates
    assert "BAR" not in result.duplicates
