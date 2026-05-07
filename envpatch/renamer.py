"""Rename keys across an EnvFile, preserving order, comments, and blank lines."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class RenameResult:
    """Result of a bulk rename operation."""

    env_file: EnvFile
    renamed: List[str] = field(default_factory=list)   # original keys that were renamed
    not_found: List[str] = field(default_factory=list)  # requested keys that did not exist

    @property
    def rename_count(self) -> int:
        return len(self.renamed)

    @property
    def has_missing(self) -> bool:
        return bool(self.not_found)


def rename_key(entry: EnvEntry, new_key: str) -> EnvEntry:
    """Return a copy of *entry* with the key replaced by *new_key*."""
    return EnvEntry(
        key=new_key,
        value=entry.value,
        comment=entry.comment,
        raw_line=None,  # raw_line is no longer accurate after rename
    )


def rename_keys(env: EnvFile, mapping: Dict[str, str]) -> RenameResult:
    """Rename multiple keys in *env* according to *mapping* (old_key -> new_key).

    - Keys not present in the file are recorded in ``not_found``.
    - Non-key entries (comments, blank lines) are preserved as-is.
    - If a target name already exists in the file the rename still proceeds;
      callers that need uniqueness enforcement should validate beforehand.
    """
    renamed: List[str] = []
    not_found: List[str] = []

    existing_keys = {e.key for e in env.entries if e.key is not None}
    for old_key in mapping:
        if old_key not in existing_keys:
            not_found.append(old_key)

    new_entries: List[EnvEntry] = []
    for entry in env.entries:
        if entry.key is not None and entry.key in mapping:
            new_entries.append(rename_key(entry, mapping[entry.key]))
            renamed.append(entry.key)
        else:
            new_entries.append(entry)

    new_env = EnvFile(entries=new_entries, path=env.path)
    return RenameResult(env_file=new_env, renamed=renamed, not_found=not_found)


def rename_key_in_file(
    env: EnvFile, old_key: str, new_key: str
) -> Optional[RenameResult]:
    """Convenience wrapper to rename a single key.  Returns None if not found."""
    result = rename_keys(env, {old_key: new_key})
    if result.has_missing:
        return None
    return result
