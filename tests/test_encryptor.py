"""Tests for envpatch.encryptor."""

import pytest

pytest.importorskip("cryptography", reason="cryptography package required")

from envpatch.encryptor import (
    decrypt_env_file,
    encrypt_env_file,
    generate_key,
)
from envpatch.parser import EnvEntry, EnvFile


def kv(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value)


def comment(text: str) -> EnvEntry:
    return EnvEntry(raw=f"# {text}")


def make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_generate_key_returns_string():
    key = generate_key()
    assert isinstance(key, str)
    assert len(key) > 0


def test_encrypt_sensitive_key_changes_value():
    key = generate_key()
    env = make_env(kv("DB_PASSWORD", "secret123"))
    result = encrypt_env_file(env, key)
    assert "DB_PASSWORD" in result.encrypted_keys
    assert result.entries[0].value != "secret123"


def test_encrypt_non_sensitive_key_unchanged_when_sensitive_only():
    key = generate_key()
    env = make_env(kv("APP_NAME", "myapp"))
    result = encrypt_env_file(env, key, sensitive_only=True)
    assert result.entries[0].value == "myapp"
    assert "APP_NAME" not in result.encrypted_keys


def test_encrypt_all_keys_when_sensitive_only_false():
    key = generate_key()
    env = make_env(kv("APP_NAME", "myapp"))
    result = encrypt_env_file(env, key, sensitive_only=False)
    assert "APP_NAME" in result.encrypted_keys
    assert result.entries[0].value != "myapp"


def test_decrypt_restores_original_value():
    key = generate_key()
    env = make_env(kv("DB_PASSWORD", "secret123"))
    encrypted = encrypt_env_file(env, key)
    decrypted = decrypt_env_file(encrypted.as_env_file, key)
    assert decrypted.entries[0].value == "secret123"
    assert "DB_PASSWORD" in decrypted.encrypted_keys


def test_decrypt_wrong_key_adds_to_failed():
    key1 = generate_key()
    key2 = generate_key()
    env = make_env(kv("API_SECRET", "topsecret"))
    encrypted = encrypt_env_file(env, key1)
    result = decrypt_env_file(encrypted.as_env_file, key2)
    assert "API_SECRET" in result.failed_keys


def test_comment_entries_passed_through():
    key = generate_key()
    env = make_env(comment("this is a comment"), kv("DB_PASSWORD", "pw"))
    result = encrypt_env_file(env, key)
    assert result.entries[0].key is None
    assert result.entries[0].raw == "# this is a comment"


def test_none_value_entry_passed_through():
    key = generate_key()
    env = make_env(kv("EMPTY_VAR", ""))
    # Force value to None
    env.entries[0] = EnvEntry(key="EMPTY_VAR", value=None)
    result = encrypt_env_file(env, key)
    assert result.entries[0].value is None
    assert "EMPTY_VAR" not in result.encrypted_keys


def test_encrypt_multiple_sensitive_keys():
    key = generate_key()
    env = make_env(
        kv("DB_PASSWORD", "pass1"),
        kv("APP_NAME", "app"),
        kv("API_SECRET", "s3cr3t"),
    )
    result = encrypt_env_file(env, key)
    assert set(result.encrypted_keys) == {"DB_PASSWORD", "API_SECRET"}
    assert result.entries[1].value == "app"


def test_as_env_file_property_returns_env_file():
    key = generate_key()
    env = make_env(kv("DB_PASSWORD", "pw"))
    result = encrypt_env_file(env, key)
    from envpatch.parser import EnvFile
    assert isinstance(result.as_env_file, EnvFile)
