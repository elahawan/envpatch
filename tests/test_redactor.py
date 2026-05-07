"""Tests for envpatch.redactor."""

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.redactor import (
    RedactorOptions,
    redact_entry,
    redact_env_file,
    list_sensitive_keys,
    DEFAULT_MASK,
)


def kv(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, original_line=f"{key}={value}")


def make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# redact_entry
# ---------------------------------------------------------------------------

def test_non_sensitive_key_unchanged():
    entry = kv("APP_NAME", "myapp")
    result = redact_entry(entry, RedactorOptions())
    assert result.value == "myapp"


def test_password_key_is_redacted():
    entry = kv("DB_PASSWORD", "s3cr3t")
    result = redact_entry(entry, RedactorOptions())
    assert result.value == DEFAULT_MASK


def test_secret_key_is_redacted():
    entry = kv("APP_SECRET", "abc123")
    result = redact_entry(entry, RedactorOptions())
    assert result.value == DEFAULT_MASK


def test_token_key_is_redacted():
    entry = kv("GITHUB_TOKEN", "ghp_xyz")
    result = redact_entry(entry, RedactorOptions())
    assert result.value == DEFAULT_MASK


def test_api_key_is_redacted():
    entry = kv("STRIPE_API_KEY", "sk_live_abc")
    result = redact_entry(entry, RedactorOptions())
    assert result.value == DEFAULT_MASK


def test_reveal_length_mask():
    entry = kv("DB_PASSWORD", "hello")
    opts = RedactorOptions(reveal_length=True)
    result = redact_entry(entry, opts)
    assert result.value == "*****"


def test_custom_mask():
    entry = kv("AUTH_TOKEN", "secret")
    opts = RedactorOptions(mask="<hidden>")
    result = redact_entry(entry, opts)
    assert result.value == "<hidden>"


def test_key_metadata_preserved():
    entry = kv("DB_PASSWORD", "s3cr3t")
    result = redact_entry(entry, RedactorOptions())
    assert result.key == "DB_PASSWORD"
    assert result.original_line == entry.original_line


def test_comment_entry_passthrough():
    entry = EnvEntry(key=None, value=None, comment="# just a comment", original_line="# just a comment")
    result = redact_entry(entry, RedactorOptions())
    assert result is entry


# ---------------------------------------------------------------------------
# redact_env_file
# ---------------------------------------------------------------------------

def test_redact_env_file_only_masks_sensitive():
    env = make_env(kv("APP_NAME", "myapp"), kv("DB_PASSWORD", "secret"))
    result = redact_env_file(env)
    d = {e.key: e.value for e in result.entries if e.key}
    assert d["APP_NAME"] == "myapp"
    assert d["DB_PASSWORD"] == DEFAULT_MASK


def test_redact_env_file_returns_new_object():
    env = make_env(kv("DB_PASSWORD", "secret"))
    result = redact_env_file(env)
    assert result is not env


# ---------------------------------------------------------------------------
# list_sensitive_keys
# ---------------------------------------------------------------------------

def test_list_sensitive_keys_finds_expected():
    env = make_env(kv("APP_NAME", "x"), kv("DB_PASSWORD", "y"), kv("API_KEY", "z"))
    keys = list_sensitive_keys(env)
    assert "DB_PASSWORD" in keys
    assert "API_KEY" in keys
    assert "APP_NAME" not in keys


def test_list_sensitive_keys_empty_file():
    env = make_env()
    assert list_sensitive_keys(env) == []


def test_custom_patterns_override():
    env = make_env(kv("MY_CUSTOM_FIELD", "value"), kv("DB_PASSWORD", "secret"))
    opts = RedactorOptions(patterns=[r"(?i)custom"])
    keys = list_sensitive_keys(env, opts)
    assert "MY_CUSTOM_FIELD" in keys
    assert "DB_PASSWORD" not in keys
