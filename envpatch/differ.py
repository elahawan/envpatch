"""Diff two EnvFile instances and report added, removed, and changed entries."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from envpatch.parser import EnvFile


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


@dataclass
class DiffEntry:
    key: str
    change_type: ChangeType
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __repr__(self) -> str:
        if self.change_type == ChangeType.ADDED:
            return f"+ {self.key}={self.new_value}"
        if self.change_type == ChangeType.REMOVED:
            return f"- {self.key}={self.old_value}"
        if self.change_type == ChangeType.CHANGED:
            return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"
        return f"  {self.key}={self.old_value}"


@dataclass
class DiffResult:
    entries: List[DiffEntry]

    @property
    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.change_type == ChangeType.ADDED]

    @property
    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.change_type == ChangeType.REMOVED]

    @property
    def changed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.change_type == ChangeType.CHANGED]

    @property
    def unchanged(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.change_type == ChangeType.UNCHANGED]

    @property
    def has_conflicts(self) -> bool:
        return bool(self.changed or self.removed)

    def summary(self) -> str:
        lines = []
        for entry in self.entries:
            lines.append(repr(entry))
        return "\n".join(lines)


def diff(base: EnvFile, target: EnvFile) -> DiffResult:
    """Compare *base* against *target* and return a DiffResult.

    Keys present only in *target* are ADDED.
    Keys present only in *base* are REMOVED.
    Keys present in both with different values are CHANGED.
    Keys present in both with the same value are UNCHANGED.
    """
    base_dict: Dict[str, str] = base.as_dict()
    target_dict: Dict[str, str] = target.as_dict()

    all_keys = list(base_dict.keys()) + [
        k for k in target_dict if k not in base_dict
    ]

    entries: List[DiffEntry] = []
    for key in all_keys:
        in_base = key in base_dict
        in_target = key in target_dict

        if in_base and in_target:
            if base_dict[key] == target_dict[key]:
                entries.append(DiffEntry(key, ChangeType.UNCHANGED, old_value=base_dict[key], new_value=target_dict[key]))
            else:
                entries.append(DiffEntry(key, ChangeType.CHANGED, old_value=base_dict[key], new_value=target_dict[key]))
        elif in_target:
            entries.append(DiffEntry(key, ChangeType.ADDED, new_value=target_dict[key]))
        else:
            entries.append(DiffEntry(key, ChangeType.REMOVED, old_value=base_dict[key]))

    return DiffResult(entries=entries)
