"""Tests for envpatch.templater."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.templater import TemplateOptions, generate_template


def make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), path=None)


def kv(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", comment=None)


def comment(text: str) -> EnvEntry:
    return EnvEntry(key=None, value=None, raw=f"# {text}", comment=None)


def blank() -> EnvEntry:
    return EnvEntry(key=None, value=None, raw="", comment=None)


# ---------------------------------------------------------------------------
# Basic redaction
# ---------------------------------------------------------------------------

def test_generate_template_replaces_values():
    env = make_env(kv("DB_HOST", "localhost"), kv("DB_PASS", "secret"))
    result = generate_template(env)
    d = {e.key: e.value for e in result.entries if e.key}
    assert d["DB_HOST"] == "<value>"
    assert d["DB_PASS"] == "<value>"


def test_generate_template_custom_placeholder():
    env = make_env(kv("API_KEY", "abc123"))
    opts = TemplateOptions(placeholder="CHANGE_ME")
    result = generate_template(env, opts)
    assert result.entries[0].value == "CHANGE_ME"


def test_generate_template_preserves_key_names():
    env = make_env(kv("FOO", "bar"), kv("BAZ", "qux"))
    result = generate_template(env)
    keys = [e.key for e in result.entries if e.key]
    assert keys == ["FOO", "BAZ"]


# ---------------------------------------------------------------------------
# Comments and blank lines
# ---------------------------------------------------------------------------

def test_comments_preserved_by_default():
    env = make_env(comment("section header"), kv("X", "1"))
    result = generate_template(env)
    assert result.entries[0].raw == "# section header"


def test_comments_stripped_when_disabled():
    env = make_env(comment("section header"), kv("X", "1"))
    opts = TemplateOptions(preserve_comments=False)
    result = generate_template(env, opts)
    keys_and_comments = [e for e in result.entries if e.raw.startswith("#")]
    assert keys_and_comments == []


def test_blank_lines_preserved_by_default():
    env = make_env(kv("A", "1"), blank(), kv("B", "2"))
    result = generate_template(env)
    assert any(e.raw == "" for e in result.entries)


def test_blank_lines_stripped_when_disabled():
    env = make_env(kv("A", "1"), blank(), kv("B", "2"))
    opts = TemplateOptions(preserve_blank_lines=False)
    result = generate_template(env, opts)
    assert not any(e.raw == "" for e in result.entries)


# ---------------------------------------------------------------------------
# Selective redaction via pattern
# ---------------------------------------------------------------------------

def test_redact_pattern_only_matches():
    env = make_env(kv("DB_PASS", "secret"), kv("APP_NAME", "myapp"))
    opts = TemplateOptions(redact_pattern="PASS")
    result = generate_template(env, opts)
    d = {e.key: e.value for e in result.entries if e.key}
    assert d["DB_PASS"] == "<value>"
    assert d["APP_NAME"] == "myapp"  # unchanged


def test_redact_pattern_no_match_keeps_all_values():
    env = make_env(kv("FOO", "bar"))
    opts = TemplateOptions(redact_pattern="SECRET")
    result = generate_template(env, opts)
    assert result.entries[0].value == "bar"
