"""Tests for envpatch.profiler."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.profiler import profile_env_file, ProfileReport


def kv(key: str, value: str, raw: str | None = None) -> EnvEntry:
    raw = raw or f"{key}={value}\n"
    return EnvEntry(key=key, value=value, raw=raw)


def comment(text: str = "# comment") -> EnvEntry:
    return EnvEntry(key=None, value=None, raw=f"{text}\n")


def blank() -> EnvEntry:
    return EnvEntry(key=None, value=None, raw="\n")


def make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_empty_file_all_zeros():
    report = profile_env_file(make_env())
    assert report.key_count == 0
    assert report.total_lines == 0


def test_key_count():
    env = make_env(kv("A", "1"), kv("B", "2"))
    report = profile_env_file(env)
    assert report.key_count == 2


def test_comment_count():
    env = make_env(comment(), comment("# another"), kv("A", "1"))
    report = profile_env_file(env)
    assert report.comment_count == 2


def test_blank_count():
    env = make_env(blank(), blank(), kv("X", "y"))
    report = profile_env_file(env)
    assert report.blank_count == 2


def test_empty_value_count():
    env = make_env(kv("A", ""), kv("B", "hello"), kv("C", ""))
    report = profile_env_file(env)
    assert report.empty_value_count == 2


def test_sensitive_key_count():
    env = make_env(kv("DB_PASSWORD", "secret"), kv("API_KEY", "abc"), kv("HOST", "localhost"))
    report = profile_env_file(env)
    assert report.sensitive_key_count == 2


def test_quoted_value_count():
    env = make_env(
        kv("A", "hello", 'A="hello"\n'),
        kv("B", "world", "B='world'\n"),
        kv("C", "plain", "C=plain\n"),
    )
    report = profile_env_file(env)
    assert report.quoted_value_count == 2


def test_duplicate_keys_detected():
    env = make_env(kv("A", "1"), kv("A", "2"), kv("B", "3"))
    report = profile_env_file(env)
    assert "A" in report.duplicate_keys
    assert "B" not in report.duplicate_keys


def test_no_duplicates_empty_list():
    env = make_env(kv("A", "1"), kv("B", "2"))
    report = profile_env_file(env)
    assert report.duplicate_keys == []


def test_longest_key():
    env = make_env(kv("SHORT", "a"), kv("MUCH_LONGER_KEY", "b"))
    report = profile_env_file(env)
    assert report.longest_key == "MUCH_LONGER_KEY"


def test_longest_value_length():
    env = make_env(kv("A", "hi"), kv("B", "a" * 50))
    report = profile_env_file(env)
    assert report.longest_value_length == 50


def test_summary_contains_key_count():
    env = make_env(kv("A", "1"), kv("B", "2"))
    report = profile_env_file(env)
    summary = report.summary()
    assert "Keys" in summary
    assert "2" in summary


def test_total_lines_counts_all_entry_types():
    env = make_env(blank(), comment(), kv("A", "1"))
    report = profile_env_file(env)
    assert report.total_lines == 3
