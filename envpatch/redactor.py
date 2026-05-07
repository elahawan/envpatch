"""Redactor module: masks sensitive values in env files before display or export."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvFile, EnvEntry

# Default patterns that indicate a key holds sensitive data
DEFAULT_SENSITIVE_PATTERNS: List[str] = [
    r"(?i)password",
    r"(?i)secret",
    r"(?i)token",
    r"(?i)api[_\-]?key",
    r"(?i)private[_\-]?key",
    r"(?i)auth",
    r"(?i)credential",
    r"(?i)passphrase",
]

DEFAULT_MASK = "***REDACTED***"


@dataclass
class RedactorOptions:
    patterns: List[str] = field(default_factory=lambda: list(DEFAULT_SENSITIVE_PATTERNS))
    mask: str = DEFAULT_MASK
    reveal_length: bool = False  # if True, mask shows original value length


def _is_sensitive(key: str, patterns: List[str]) -> bool:
    """Return True if the key matches any sensitive pattern."""
    return any(re.search(p, key) for p in patterns)


def _make_mask(value: Optional[str], options: RedactorOptions) -> str:
    """Build the mask string, optionally encoding value length."""
    if options.reveal_length and value:
        return f"{'*' * len(value)}"
    return options.mask


def redact_entry(entry: EnvEntry, options: RedactorOptions) -> EnvEntry:
    """Return a copy of *entry* with the value masked if the key is sensitive."""
    if entry.key is None:
        return entry
    if _is_sensitive(entry.key, options.patterns):
        masked = _make_mask(entry.value, options)
        return EnvEntry(
            key=entry.key,
            value=masked,
            comment=entry.comment,
            original_line=entry.original_line,
        )
    return entry


def redact_env_file(env_file: EnvFile, options: Optional[RedactorOptions] = None) -> EnvFile:
    """Return a new EnvFile where all sensitive values have been redacted."""
    opts = options or RedactorOptions()
    redacted_entries = [redact_entry(e, opts) for e in env_file.entries]
    return EnvFile(entries=redacted_entries)


def list_sensitive_keys(env_file: EnvFile, options: Optional[RedactorOptions] = None) -> List[str]:
    """Return the list of keys considered sensitive in *env_file*."""
    opts = options or RedactorOptions()
    return [
        e.key
        for e in env_file.entries
        if e.key is not None and _is_sensitive(e.key, opts.patterns)
    ]
