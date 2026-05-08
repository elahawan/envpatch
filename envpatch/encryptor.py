"""Encrypt and decrypt sensitive values in .env files using Fernet symmetric encryption."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvEntry, EnvFile
from envpatch.redactor import _is_sensitive

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore


@dataclass
class EncryptionResult:
    entries: List[EnvEntry]
    encrypted_keys: List[str] = field(default_factory=list)
    failed_keys: List[str] = field(default_factory=list)

    @property
    def as_env_file(self) -> EnvFile:
        return EnvFile(entries=self.entries)


def generate_key() -> str:
    """Generate a new Fernet key as a URL-safe base64 string."""
    if Fernet is None:
        raise RuntimeError("cryptography package is required: pip install cryptography")
    return Fernet.generate_key().decode()


def _get_fernet(key: str) -> "Fernet":
    if Fernet is None:
        raise RuntimeError("cryptography package is required: pip install cryptography")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_env_file(
    env_file: EnvFile,
    key: str,
    sensitive_only: bool = True,
) -> EncryptionResult:
    """Return a new EnvFile with sensitive (or all) values encrypted."""
    fernet = _get_fernet(key)
    new_entries: List[EnvEntry] = []
    encrypted_keys: List[str] = []
    failed_keys: List[str] = []

    for entry in env_file.entries:
        if entry.key is None or entry.value is None:
            new_entries.append(entry)
            continue
        if sensitive_only and not _is_sensitive(entry.key):
            new_entries.append(entry)
            continue
        try:
            encrypted = fernet.encrypt(entry.value.encode()).decode()
            new_entries.append(EnvEntry(key=entry.key, value=encrypted, comment=entry.comment))
            encrypted_keys.append(entry.key)
        except Exception:
            new_entries.append(entry)
            failed_keys.append(entry.key)

    return EncryptionResult(entries=new_entries, encrypted_keys=encrypted_keys, failed_keys=failed_keys)


def decrypt_env_file(
    env_file: EnvFile,
    key: str,
    sensitive_only: bool = True,
) -> EncryptionResult:
    """Return a new EnvFile with encrypted values decrypted."""
    fernet = _get_fernet(key)
    new_entries: List[EnvEntry] = []
    decrypted_keys: List[str] = []
    failed_keys: List[str] = []

    for entry in env_file.entries:
        if entry.key is None or entry.value is None:
            new_entries.append(entry)
            continue
        if sensitive_only and not _is_sensitive(entry.key):
            new_entries.append(entry)
            continue
        try:
            decrypted = fernet.decrypt(entry.value.encode()).decode()
            new_entries.append(EnvEntry(key=entry.key, value=decrypted, comment=entry.comment))
            decrypted_keys.append(entry.key)
        except InvalidToken:
            new_entries.append(entry)
            failed_keys.append(entry.key)

    return EncryptionResult(entries=new_entries, encrypted_keys=decrypted_keys, failed_keys=failed_keys)
