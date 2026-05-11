"""Detect and remove duplicate keys from an .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class DeduplicateResult:
    """Result of a deduplication pass over an EnvFile."""

    entries: List[EnvEntry]
    duplicates: Dict[str, List[int]]  # key -> list of line indices that were duplicates

    @property
    def duplicate_count(self) -> int:
        """Total number of duplicate entries removed."""
        return sum(len(v) for v in self.duplicates.values())

    @property
    def was_modified(self) -> bool:
        """True if any duplicates were removed."""
        return bool(self.duplicates)

    def as_env_file(self) -> EnvFile:
        """Return deduplicated entries as a new EnvFile."""
        return EnvFile(entries=self.entries)


def deduplicate_env_file(
    env: EnvFile,
    keep: str = "last",
) -> DeduplicateResult:
    """Remove duplicate keys from *env*, keeping either the first or last occurrence.

    Args:
        env: The parsed environment file.
        keep: ``"first"`` keeps the first occurrence; ``"last"`` keeps the last.

    Returns:
        A :class:`DeduplicateResult` describing what was removed.
    """
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    # Collect indices for each key (non-comment, non-blank entries only)
    key_indices: Dict[str, List[int]] = {}
    for idx, entry in enumerate(env.entries):
        if entry.key is None:
            continue
        key_indices.setdefault(entry.key, []).append(idx)

    # Determine which indices to drop
    drop: set[int] = set()
    duplicates: Dict[str, List[int]] = {}
    for key, indices in key_indices.items():
        if len(indices) < 2:
            continue
        if keep == "first":
            removed = indices[1:]
        else:
            removed = indices[:-1]
        drop.update(removed)
        duplicates[key] = removed

    kept_entries = [
        entry for idx, entry in enumerate(env.entries) if idx not in drop
    ]
    return DeduplicateResult(entries=kept_entries, duplicates=duplicates)
