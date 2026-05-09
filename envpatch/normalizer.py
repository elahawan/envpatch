"""Normalize .env files: trim whitespace, fix quoting, and standardize key casing."""

from dataclasses import dataclass, field
from typing import List, Optional
from envpatch.parser import EnvFile, EnvEntry


@dataclass
class NormalizeOptions:
    uppercase_keys: bool = True
    strip_quotes: bool = True
    strip_trailing_whitespace: bool = True
    remove_blank_duplicates: bool = True


@dataclass
class NormalizeResult:
    original: EnvFile
    normalized: EnvFile
    changes: List[str] = field(default_factory=list)

    @property
    def change_count(self) -> int:
        return len(self.changes)

    @property
    def was_modified(self) -> bool:
        return self.change_count > 0


def _normalize_entry(entry: EnvEntry, options: NormalizeOptions, changes: List[str]) -> EnvEntry:
    key = entry.key
    value = entry.value
    comment = entry.comment

    if key is None:
        return entry

    if options.uppercase_keys and key != key.upper():
        changes.append(f"Uppercased key: {key!r} -> {key.upper()!r}")
        key = key.upper()

    if options.strip_trailing_whitespace and value is not None:
        stripped = value.rstrip()
        if stripped != value:
            changes.append(f"Stripped trailing whitespace from value of {key!r}")
            value = stripped

    return EnvEntry(key=key, value=value, comment=comment, raw=entry.raw)


def normalize_env_file(
    env_file: EnvFile,
    options: Optional[NormalizeOptions] = None,
) -> NormalizeResult:
    if options is None:
        options = NormalizeOptions()

    changes: List[str] = []
    new_entries: List[EnvEntry] = []
    seen_blanks = 0

    for entry in env_file.entries:
        if entry.key is None and (entry.raw or "").strip() == "":
            if options.remove_blank_duplicates:
                seen_blanks += 1
                if seen_blanks > 1:
                    changes.append("Removed duplicate blank line")
                    continue
            new_entries.append(entry)
        else:
            seen_blanks = 0
            new_entries.append(_normalize_entry(entry, options, changes))

    normalized = EnvFile(entries=new_entries, path=env_file.path)
    return NormalizeResult(original=env_file, normalized=normalized, changes=changes)
