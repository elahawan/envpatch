"""Tests for envpatch.validator."""

import pytest

from envpatch.parser import EnvFile
from envpatch.validator import validate_env_file, ValidationResult, ValidationIssue


def parse(text: str) -> EnvFile:
    return EnvFile.parse(text)


def test_valid_file_no_issues():
    text = "KEY=value\nANOTHER=123\n"
    env = parse(text)
    result = validate_env_file(env, text)
    assert result.is_valid()
    assert result.issues == []


def test_comment_lines_ignored():
    text = "# this is a comment\nKEY=value\n"
    env = parse(text)
    result = validate_env_file(env, text)
    assert result.is_valid()


def test_blank_lines_ignored():
    text = "\nKEY=value\n\n"
    env = parse(text)
    result = validate_env_file(env, text)
    assert result.is_valid()


def test_missing_equals_is_error():
    text = "BADLINE\nKEY=value\n"
    env = parse(text)
    result = validate_env_file(env, text)
    assert not result.is_valid()
    assert len(result.errors()) == 1
    assert result.errors()[0].line == 1


def test_empty_key_is_error():
    text = "=value\n"
    env = parse(text)
    result = validate_env_file(env, text)
    assert not result.is_valid()
    errors = result.errors()
    assert any("empty key" in e.message for e in errors)


def test_duplicate_key_is_warning():
    text = "KEY=first\nKEY=second\n"
    env = parse(text)
    result = validate_env_file(env, text)
    assert result.is_valid()  # warning, not error
    warnings = result.warnings()
    assert len(warnings) == 1
    assert "duplicate" in warnings[0].message
    assert warnings[0].key == "KEY"


def test_key_with_spaces_is_warning():
    text = "MY KEY=value\n"
    env = parse(text)
    result = validate_env_file(env, text)
    warnings = result.warnings()
    assert any("spaces" in w.message for w in warnings)


def test_validation_issue_str():
    issue = ValidationIssue(line=3, key="FOO", message="something wrong", severity="error")
    s = str(issue)
    assert "ERROR" in s
    assert "line 3" in s
    assert "FOO" in s
    assert "something wrong" in s


def test_validation_result_errors_and_warnings():
    result = ValidationResult(issues=[
        ValidationIssue(line=1, key=None, message="bad", severity="error"),
        ValidationIssue(line=2, key="X", message="dup", severity="warning"),
    ])
    assert not result.is_valid()
    assert len(result.errors()) == 1
    assert len(result.warnings()) == 1
