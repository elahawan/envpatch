"""Tests for envpatch.normalizer."""

import pytest
from envpatch.parser import EnvFile, EnvEntry
from envpatch.normalizer import NormalizeOptions, NormalizeResult, normalize_env_file


def kv(key, value, comment=None):
    raw = f"{key}={value}"
    return EnvEntry(key=key, value=value, comment=comment, raw=raw)


def blank():
    return EnvEntry(key=None, value=None, comment=None, raw="")


def comment_line(text):
    return EnvEntry(key=None, value=None, comment=text, raw=f"# {text}")


def make_env(*entries):
    return EnvFile(entries=list(entries), path=None)


def test_normalize_returns_result():
    env = make_env(kv("foo", "bar"))
    result = normalize_env_file(env)
    assert isinstance(result, NormalizeResult)


def test_uppercase_keys_by_default():
    env = make_env(kv("db_host", "localhost"))
    result = normalize_env_file(env)
    keys = [e.key for e in result.normalized.entries if e.key]
    assert keys == ["DB_HOST"]


def test_uppercase_keys_records_change():
    env = make_env(kv("db_host", "localhost"))
    result = normalize_env_file(env)
    assert any("DB_HOST" in c for c in result.changes)


def test_already_uppercase_no_change():
    env = make_env(kv("DB_HOST", "localhost"))
    result = normalize_env_file(env)
    assert not result.was_modified


def test_uppercase_disabled():
    opts = NormalizeOptions(uppercase_keys=False)
    env = make_env(kv("db_host", "localhost"))
    result = normalize_env_file(env, opts)
    keys = [e.key for e in result.normalized.entries if e.key]
    assert keys == ["db_host"]


def test_strip_trailing_whitespace():
    env = make_env(kv("API_KEY", "abc123   "))
    result = normalize_env_file(env)
    values = [e.value for e in result.normalized.entries if e.key]
    assert values == ["abc123"]


def test_strip_trailing_whitespace_records_change():
    env = make_env(kv("API_KEY", "abc   "))
    result = normalize_env_file(env)
    assert any("API_KEY" in c for c in result.changes)


def test_strip_trailing_whitespace_disabled():
    opts = NormalizeOptions(strip_trailing_whitespace=False)
    env = make_env(kv("API_KEY", "abc   "))
    result = normalize_env_file(env, opts)
    values = [e.value for e in result.normalized.entries if e.key]
    assert values == ["abc   "]


def test_remove_duplicate_blank_lines():
    env = make_env(kv("A", "1"), blank(), blank(), kv("B", "2"))
    result = normalize_env_file(env)
    blank_count = sum(1 for e in result.normalized.entries if e.key is None and (e.raw or "").strip() == "")
    assert blank_count == 1


def test_remove_duplicate_blank_lines_records_change():
    env = make_env(blank(), blank())
    result = normalize_env_file(env)
    assert any("blank" in c.lower() for c in result.changes)


def test_single_blank_line_preserved():
    env = make_env(kv("A", "1"), blank(), kv("B", "2"))
    result = normalize_env_file(env)
    assert not result.was_modified


def test_comment_lines_preserved():
    env = make_env(comment_line("this is a comment"), kv("A", "1"))
    result = normalize_env_file(env)
    assert len(result.normalized.entries) == 2


def test_change_count_reflects_all_changes():
    env = make_env(kv("foo", "bar   "), blank(), blank())
    result = normalize_env_file(env)
    assert result.change_count >= 2
