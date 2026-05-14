"""Tests for envpatch.filter module."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.filter import FilterOptions, FilterResult, filter_env_file


def kv(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}")


def comment(text: str = "# comment") -> EnvEntry:
    return EnvEntry(key=None, value=None, raw=text)


def blank() -> EnvEntry:
    return EnvEntry(key=None, value=None, raw="")


def make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_no_options_returns_all_entries():
    env = make_env(kv("DB_HOST"), kv("API_KEY"), kv("PORT"))
    result = filter_env_file(env)
    assert result.match_count == 3
    assert result.excluded_count == 0


def test_prefix_filter_matches_prefix():
    env = make_env(kv("DB_HOST"), kv("DB_PORT"), kv("API_KEY"))
    opts = FilterOptions(prefixes=["DB_"])
    result = filter_env_file(env, opts)
    keys = [e.key for e in result.matched.entries if e.key]
    assert keys == ["DB_HOST", "DB_PORT"]


def test_prefix_filter_excludes_non_matching():
    env = make_env(kv("DB_HOST"), kv("API_KEY"))
    opts = FilterOptions(prefixes=["DB_"])
    result = filter_env_file(env, opts)
    excluded_keys = [e.key for e in result.excluded.entries if e.key]
    assert "API_KEY" in excluded_keys


def test_pattern_filter_uses_glob():
    env = make_env(kv("AWS_ACCESS_KEY"), kv("AWS_SECRET"), kv("PORT"))
    opts = FilterOptions(patterns=["AWS_*"])
    result = filter_env_file(env, opts)
    keys = [e.key for e in result.matched.entries if e.key]
    assert "AWS_ACCESS_KEY" in keys
    assert "AWS_SECRET" in keys
    assert "PORT" not in keys


def test_exclude_prefix_removes_matching():
    env = make_env(kv("SECRET_KEY"), kv("SECRET_SALT"), kv("HOST"))
    opts = FilterOptions(exclude_prefixes=["SECRET_"])
    result = filter_env_file(env, opts)
    keys = [e.key for e in result.matched.entries if e.key]
    assert keys == ["HOST"]


def test_exclude_pattern_removes_matching():
    env = make_env(kv("DB_PASSWORD"), kv("API_TOKEN"), kv("PORT"))
    opts = FilterOptions(exclude_patterns=["*PASSWORD", "*TOKEN"])
    result = filter_env_file(env, opts)
    keys = [e.key for e in result.matched.entries if e.key]
    assert keys == ["PORT"]


def test_only_empty_filters_to_empty_values():
    env = make_env(kv("A", ""), kv("B", "something"), kv("C", ""))
    opts = FilterOptions(only_empty=True)
    result = filter_env_file(env, opts)
    keys = [e.key for e in result.matched.entries if e.key]
    assert keys == ["A", "C"]


def test_only_nonempty_filters_to_set_values():
    env = make_env(kv("A", ""), kv("B", "hello"), kv("C", ""))
    opts = FilterOptions(only_nonempty=True)
    result = filter_env_file(env, opts)
    keys = [e.key for e in result.matched.entries if e.key]
    assert keys == ["B"]


def test_comments_and_blanks_always_pass_through():
    env = make_env(comment("# header"), blank(), kv("API_KEY"))
    opts = FilterOptions(prefixes=["DB_"])
    result = filter_env_file(env, opts)
    raw_lines = [e.raw for e in result.matched.entries]
    assert "# header" in raw_lines
    assert "" in raw_lines


def test_match_count_excludes_non_kv_entries():
    env = make_env(comment(), blank(), kv("X"), kv("Y"))
    result = filter_env_file(env)
    assert result.match_count == 2


def test_combined_prefix_and_exclude_pattern():
    env = make_env(kv("DB_HOST"), kv("DB_PASSWORD"), kv("API_KEY"))
    opts = FilterOptions(prefixes=["DB_"], exclude_patterns=["*PASSWORD"])
    result = filter_env_file(env, opts)
    keys = [e.key for e in result.matched.entries if e.key]
    assert keys == ["DB_HOST"]
