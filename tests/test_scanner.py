"""Tests for envpatch.scanner."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.scanner import (
    ScanSeverity,
    ScanIssue,
    ScanReport,
    scan_env_file,
)


def kv(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, raw=f"{key}={value}")


def comment(text: str) -> EnvEntry:
    return EnvEntry(key=None, value=None, comment=text, raw=f"# {text}")


def make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_clean_file_returns_no_issues():
    env = make_env(kv("APP_NAME", "myapp"), kv("PORT", "8080"))
    report = scan_env_file(env)
    assert report.is_clean
    assert report.issues == []


def test_sensitive_placeholder_raises_s001():
    env = make_env(kv("DB_PASSWORD", "changeme"))
    report = scan_env_file(env)
    codes = [i.code for i in report.issues]
    assert "S001" in codes


def test_sensitive_placeholder_is_error():
    env = make_env(kv("API_SECRET", "placeholder"))
    report = scan_env_file(env)
    s001 = next(i for i in report.issues if i.code == "S001")
    assert s001.severity == ScanSeverity.ERROR


def test_sensitive_empty_value_raises_s002():
    env = make_env(kv("AUTH_TOKEN", ""))
    report = scan_env_file(env)
    codes = [i.code for i in report.issues]
    assert "S002" in codes


def test_sensitive_empty_value_is_warning():
    env = make_env(kv("AUTH_TOKEN", ""))
    report = scan_env_file(env)
    s002 = next(i for i in report.issues if i.code == "S002")
    assert s002.severity == ScanSeverity.WARNING


def test_non_sensitive_empty_value_no_issue():
    env = make_env(kv("APP_NAME", ""))
    report = scan_env_file(env)
    assert report.is_clean


def test_double_whitespace_raises_s003():
    env = make_env(kv("DESCRIPTION", "hello  world"))
    report = scan_env_file(env)
    codes = [i.code for i in report.issues]
    assert "S003" in codes


def test_comment_entries_are_skipped():
    env = make_env(comment("this is a comment"), kv("PORT", "3000"))
    report = scan_env_file(env)
    assert report.is_clean


def test_errors_property_filters_correctly():
    env = make_env(kv("DB_PASSWORD", "changeme"), kv("AUTH_TOKEN", ""))
    report = scan_env_file(env)
    assert all(i.severity == ScanSeverity.ERROR for i in report.errors)


def test_warnings_property_filters_correctly():
    env = make_env(kv("DB_PASSWORD", "changeme"), kv("AUTH_TOKEN", ""))
    report = scan_env_file(env)
    assert all(i.severity == ScanSeverity.WARNING for i in report.warnings)


def test_summary_contains_counts():
    env = make_env(kv("DB_PASSWORD", "changeme"))
    report = scan_env_file(env)
    summary = report.summary()
    assert "error" in summary
    assert "warning" in summary


def test_scan_issue_str_includes_code_and_key():
    issue = ScanIssue(
        key="MY_KEY",
        code="S001",
        message="some message",
        severity=ScanSeverity.ERROR,
    )
    text = str(issue)
    assert "S001" in text
    assert "MY_KEY" in text
    assert "ERROR" in text
