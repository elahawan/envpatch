"""Merge logic for applying diffs to .env files with conflict resolution."""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvFile, EnvEntry
from envpatch.differ import DiffResult, DiffEntry, ChangeType


class ConflictStrategy(Enum):
    OURS = "ours"
    THEIRS = "theirs"
    PROMPT = "prompt"


@dataclass
class MergeConflict:
    key: str
    base_value: Optional[str]
    incoming_value: Optional[str]
    resolved_value: Optional[str] = None

    def resolve(self, value: Optional[str]) -> None:
        self.resolved_value = value


@dataclass
class MergeResult:
    merged: EnvFile
    conflicts: List[MergeConflict] = field(default_factory=list)
    applied: List[DiffEntry] = field(default_factory=list)
    skipped: List[DiffEntry] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return any(c.resolved_value is None for c in self.conflicts)


def merge(
    base: EnvFile,
    diff: DiffResult,
    strategy: ConflictStrategy = ConflictStrategy.THEIRS,
    existing_keys_conflict: bool = True,
) -> MergeResult:
    """Apply a diff to a base EnvFile, returning a MergeResult."""
    entries = {e.key: e for e in base.entries if e.key is not None}
    result_entries: List[EnvEntry] = list(base.entries)
    conflicts: List[MergeConflict] = []
    applied: List[DiffEntry] = []
    skipped: List[DiffEntry] = []

    for change in diff.changes:
        key = change.key

        if change.change_type == ChangeType.ADDED:
            if key in entries and existing_keys_conflict:
                conflict = MergeConflict(
                    key=key,
                    base_value=entries[key].value,
                    incoming_value=change.new_value,
                )
                _resolve_conflict(conflict, strategy)
                conflicts.append(conflict)
                if conflict.resolved_value is not None:
                    _update_entry(result_entries, key, conflict.resolved_value)
                    applied.append(change)
                else:
                    skipped.append(change)
            else:
                result_entries.append(EnvEntry(key=key, value=change.new_value))
                applied.append(change)

        elif change.change_type == ChangeType.REMOVED:
            result_entries = [e for e in result_entries if e.key != key]
            applied.append(change)

        elif change.change_type == ChangeType.CHANGED:
            if key not in entries:
                skipped.append(change)
                continue
            conflict = MergeConflict(
                key=key,
                base_value=entries[key].value,
                incoming_value=change.new_value,
            )
            _resolve_conflict(conflict, strategy)
            conflicts.append(conflict)
            if conflict.resolved_value is not None:
                _update_entry(result_entries, key, conflict.resolved_value)
                applied.append(change)
            else:
                skipped.append(change)

    merged_file = EnvFile(entries=result_entries)
    return MergeResult(merged=merged_file, conflicts=conflicts, applied=applied, skipped=skipped)


def _resolve_conflict(conflict: MergeConflict, strategy: ConflictStrategy) -> None:
    if strategy == ConflictStrategy.THEIRS:
        conflict.resolved_value = conflict.incoming_value
    elif strategy == ConflictStrategy.OURS:
        conflict.resolved_value = conflict.base_value
    # PROMPT leaves resolved_value as None for external handling


def _update_entry(entries: List[EnvEntry], key: str, value: Optional[str]) -> None:
    for i, entry in enumerate(entries):
        if entry.key == key:
            entries[i] = EnvEntry(key=key, value=value, comment=entry.comment)
            return
