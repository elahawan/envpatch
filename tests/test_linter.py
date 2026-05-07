"""Tests for envpatch.linter."""

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.linter import lint_env_file, LintResult, LintIssue


def kv(key: str, value: str | None = "", is_comment: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", is_comment=is_comment)


def make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_clean_file_returns_no_issues():
    env = make_env(kv("DATABASE_URL", "postgres://localhost/db"), kv("PORT", "5432"))
    result = lint_env_file(env)
    assert result.is_clean


def test_lowercase_key_raises_e001():
    env = make_env(kv("database_url", "postgres://localhost"))
    result = lint_env_file(env)
    codes = [i.code for i in result.issues]
    assert "E001" in codes


def test_mixed_case_key_raises_e001():
    env = make_env(kv("DbHost", "localhost"))
    result = lint_env_file(env)
    assert any(i.code == "E001" for i in result.issues)


def test_uppercase_key_no_e001():
    env = make_env(kv("DB_HOST", "localhost"))
    result = lint_env_file(env)
    assert not any(i.code == "E001" for i in result.issues)


def test_key_with_space_raises_e002():
    env = make_env(kv("MY KEY", "value"))
    result = lint_env_file(env)
    assert any(i.code == "E002" for i in result.issues)


def test_key_without_space_no_e002():
    env = make_env(kv("MY_KEY", "value"))
    result = lint_env_file(env)
    assert not any(i.code == "E002" for i in result.issues)


def test_none_value_raises_w001():
    env = make_env(kv("MY_KEY", None))
    result = lint_env_file(env)
    assert any(i.code == "W001" for i in result.issues)


def test_empty_string_value_no_w001():
    env = make_env(kv("MY_KEY", ""))
    result = lint_env_file(env)
    assert not any(i.code == "W001" for i in result.issues)


def test_value_with_leading_whitespace_raises_w002():
    env = make_env(kv("MY_KEY", " value"))
    result = lint_env_file(env)
    assert any(i.code == "W002" for i in result.issues)


def test_value_with_trailing_whitespace_raises_w002():
    env = make_env(kv("MY_KEY", "value "))
    result = lint_env_file(env)
    assert any(i.code == "W002" for i in result.issues)


def test_comment_lines_are_skipped():
    entry = EnvEntry(key=None, value=None, raw="# this is a comment", is_comment=True)
    env = make_env(entry)
    result = lint_env_file(env)
    assert result.is_clean


def test_errors_filtered_by_code():
    env = make_env(kv("bad key", None))  # triggers E002 and W001 (and E001 if lowercase)
    result = lint_env_file(env)
    w001_issues = result.errors("W001")
    assert all(i.code == "W001" for i in w001_issues)


def test_lint_issue_str_representation():
    issue = LintIssue(line_number=3, key="bad_key", code="E001", message="Key should be UPPER_SNAKE_CASE")
    text = str(issue)
    assert "E001" in text
    assert "bad_key" in text
    assert "3" in text


def test_multiple_issues_on_same_entry():
    env = make_env(kv("bad key", None))  # space in key + None value
    result = lint_env_file(env)
    codes = {i.code for i in result.issues}
    assert "E002" in codes
    assert "W001" in codes
