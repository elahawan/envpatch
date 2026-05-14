"""Filter .env file entries by key patterns, prefixes, or value conditions."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class FilterOptions:
    prefixes: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    exclude_prefixes: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    only_empty: bool = False
    only_nonempty: bool = False


@dataclass
class FilterResult:
    matched: EnvFile
    excluded: EnvFile

    @property
    def match_count(self) -> int:
        return sum(1 for e in self.matched.entries if e.key is not None)

    @property
    def excluded_count(self) -> int:
        return sum(1 for e in self.excluded.entries if e.key is not None)


def _key_matches(key: str, prefixes: List[str], patterns: List[str]) -> bool:
    for prefix in prefixes:
        if key.startswith(prefix):
            return True
    for pattern in patterns:
        if fnmatch.fnmatch(key, pattern):
            return True
    return False


def _entry_passes(entry: EnvEntry, opts: FilterOptions) -> bool:
    if entry.key is None:
        return True  # preserve comments and blanks

    key = entry.key

    if opts.exclude_prefixes or opts.exclude_patterns:
        if _key_matches(key, opts.exclude_prefixes, opts.exclude_patterns):
            return False

    if opts.prefixes or opts.patterns:
        if not _key_matches(key, opts.prefixes, opts.patterns):
            return False

    if opts.only_empty and entry.value:
        return False
    if opts.only_nonempty and not entry.value:
        return False

    return True


def filter_env_file(env: EnvFile, opts: Optional[FilterOptions] = None) -> FilterResult:
    if opts is None:
        opts = FilterOptions()

    matched_entries: List[EnvEntry] = []
    excluded_entries: List[EnvEntry] = []

    for entry in env.entries:
        if _entry_passes(entry, opts):
            matched_entries.append(entry)
        else:
            excluded_entries.append(entry)

    return FilterResult(
        matched=EnvFile(entries=matched_entries),
        excluded=EnvFile(entries=excluded_entries),
    )
