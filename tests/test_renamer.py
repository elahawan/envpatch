"""Tests for envpatch.renamer."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.renamer import rename_key, rename_key_in_file, rename_keys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def kv(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, raw_line=None)


def comment(text: str) -> EnvEntry:
    return EnvEntry(key=None, value=None, comment=text, raw_line=f"# {text}")


def blank() -> EnvEntry:
    return EnvEntry(key=None, value=None, comment=None, raw_line="")


def make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), path=None)


# ---------------------------------------------------------------------------
# rename_key (single entry)
# ---------------------------------------------------------------------------

def test_rename_key_changes_key():
    entry = kv("OLD", "123")
    result = rename_key(entry, "NEW")
    assert result.key == "NEW"


def test_rename_key_preserves_value():
    entry = kv("OLD", "my_value")
    result = rename_key(entry, "NEW")
    assert result.value == "my_value"


def test_rename_key_preserves_comment():
    entry = EnvEntry(key="OLD", value="v", comment="inline", raw_line=None)
    result = rename_key(entry, "NEW")
    assert result.comment == "inline"


def test_rename_key_clears_raw_line():
    entry = EnvEntry(key="OLD", value="v", comment=None, raw_line="OLD=v")
    result = rename_key(entry, "NEW")
    assert result.raw_line is None


# ---------------------------------------------------------------------------
# rename_keys (bulk)
# ---------------------------------------------------------------------------

def test_rename_keys_single_mapping():
    env = make_env(kv("DB_HOST"), kv("DB_PORT"))
    result = rename_keys(env, {"DB_HOST": "DATABASE_HOST"})
    keys = [e.key for e in result.env_file.entries if e.key]
    assert "DATABASE_HOST" in keys
    assert "DB_HOST" not in keys


def test_rename_keys_records_renamed():
    env = make_env(kv("A"), kv("B"))
    result = rename_keys(env, {"A": "ALPHA", "B": "BETA"})
    assert sorted(result.renamed) == ["A", "B"]
    assert result.rename_count == 2


def test_rename_keys_missing_key_recorded():
    env = make_env(kv("A"))
    result = rename_keys(env, {"MISSING": "NEW"})
    assert "MISSING" in result.not_found
    assert result.has_missing is True


def test_rename_keys_preserves_comments_and_blanks():
    env = make_env(comment("header"), blank(), kv("FOO"))
    result = rename_keys(env, {"FOO": "BAR"})
    entries = result.env_file.entries
    assert entries[0].comment == "header"
    assert entries[1].raw_line == ""
    assert entries[2].key == "BAR"


def test_rename_keys_preserves_order():
    env = make_env(kv("A"), kv("B"), kv("C"))
    result = rename_keys(env, {"B": "BETA"})
    keys = [e.key for e in result.env_file.entries]
    assert keys == ["A", "BETA", "C"]


def test_rename_keys_empty_mapping_is_noop():
    env = make_env(kv("X"), kv("Y"))
    result = rename_keys(env, {})
    assert result.rename_count == 0
    assert not result.has_missing


# ---------------------------------------------------------------------------
# rename_key_in_file (convenience)
# ---------------------------------------------------------------------------

def test_rename_key_in_file_returns_result_on_success():
    env = make_env(kv("OLD"))
    result = rename_key_in_file(env, "OLD", "NEW")
    assert result is not None
    assert result.renamed == ["OLD"]


def test_rename_key_in_file_returns_none_when_not_found():
    env = make_env(kv("EXISTING"))
    result = rename_key_in_file(env, "GHOST", "NEW")
    assert result is None
