"""Integration tests for encrypt -> decrypt roundtrip across a full env file."""

import pytest

pytest.importorskip("cryptography", reason="cryptography package required")

from envpatch.encryptor import decrypt_env_file, encrypt_env_file, generate_key
from envpatch.parser import EnvEntry, EnvFile
from envpatch.serializer import serialize
from envpatch.parser import EnvFile as _EnvFile


def make_full_env() -> EnvFile:
    return EnvFile(entries=[
        EnvEntry(raw="# Database settings"),
        EnvEntry(key="DB_HOST", value="localhost"),
        EnvEntry(key="DB_PASSWORD", value="s3cr3t!"),
        EnvEntry(raw=""),
        EnvEntry(key="API_KEY", value="abc123xyz"),
        EnvEntry(key="APP_ENV", value="production"),
        EnvEntry(key="SECRET_TOKEN", value="tok_live_999"),
    ])


def test_roundtrip_preserves_all_values():
    key = generate_key()
    env = make_full_env()
    original_values = {e.key: e.value for e in env.entries if e.key}
    encrypted = encrypt_env_file(env, key)
    decrypted = decrypt_env_file(encrypted.as_env_file, key)
    for entry in decrypted.entries:
        if entry.key:
            assert entry.value == original_values[entry.key]


def test_roundtrip_preserves_structure():
    key = generate_key()
    env = make_full_env()
    encrypted = encrypt_env_file(env, key)
    decrypted = decrypt_env_file(encrypted.as_env_file, key)
    assert len(decrypted.entries) == len(env.entries)


def test_encrypted_values_differ_from_originals():
    key = generate_key()
    env = make_full_env()
    encrypted = encrypt_env_file(env, key)
    for entry in encrypted.entries:
        if entry.key in ("DB_PASSWORD", "API_KEY", "SECRET_TOKEN"):
            original = next(e for e in env.entries if e.key == entry.key)
            assert entry.value != original.value


def test_non_sensitive_keys_unchanged_after_encrypt():
    key = generate_key()
    env = make_full_env()
    encrypted = encrypt_env_file(env, key, sensitive_only=True)
    db_host = next(e for e in encrypted.entries if e.key == "DB_HOST")
    app_env = next(e for e in encrypted.entries if e.key == "APP_ENV")
    assert db_host.value == "localhost"
    assert app_env.value == "production"


def test_serialize_encrypted_file_is_valid_env():
    key = generate_key()
    env = make_full_env()
    encrypted = encrypt_env_file(env, key)
    text = serialize(encrypted.as_env_file)
    reparsed = _EnvFile.parse(text)
    kv_entries = [e for e in reparsed.entries if e.key]
    assert len(kv_entries) == 5


def test_encrypt_with_all_keys_encrypts_non_sensitive():
    key = generate_key()
    env = make_full_env()
    result = encrypt_env_file(env, key, sensitive_only=False)
    assert "DB_HOST" in result.encrypted_keys
    assert "APP_ENV" in result.encrypted_keys
