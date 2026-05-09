"""Sort and group entries in an EnvFile by key or insertion order."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from envpatch.parser import EnvEntry, EnvFile


class SortOrder(str, Enum):
    ALPHA = "alpha"          # A-Z by key
    ALPHA_DESC = "alpha_desc"  # Z-A by key
    ORIGINAL = "original"   # preserve insertion order


@dataclass
class SortOptions:
    order: SortOrder = SortOrder.ALPHA
    group_comments: bool = True   # keep comment/blank lines attached to next entry
    ignore_case: bool = True


def _sort_key(entry: EnvEntry, ignore_case: bool) -> str:
    key = entry.key or ""
    return key.lower() if ignore_case else key


def _group_entries(entries: List[EnvEntry], group_comments: bool) -> tuple[List[List[EnvEntry]], List[EnvEntry]]:
    """Partition *entries* into groups and a trailing list of comment/blank lines.

    When *group_comments* is True, consecutive comment and blank lines that
    precede a key=value entry are bundled into the same group as that entry so
    they travel with it during sorting.  Standalone comment/blank lines that
    are not followed by a kv entry are returned separately as *trailing*.

    Returns:
        groups:   list of entry groups (each group is a list of EnvEntry).
        trailing: leftover comment/blank entries after the last kv entry.
    """
    groups: List[List[EnvEntry]] = []
    pending: List[EnvEntry] = []

    for entry in entries:
        if entry.key is None:  # comment or blank
            if group_comments:
                pending.append(entry)
            else:
                groups.append([entry])
        else:
            groups.append(pending + [entry])
            pending = []

    return groups, pending


def sort_env_file(env: EnvFile, options: Optional[SortOptions] = None) -> EnvFile:
    """Return a new EnvFile with entries sorted according to *options*.

    Comment and blank lines that immediately precede a key=value entry are
    treated as belonging to that entry when *group_comments* is True, so they
    travel with it during sorting.
    """
    if options is None:
        options = SortOptions()

    if options.order is SortOrder.ORIGINAL:
        return EnvFile(entries=list(env.entries), path=env.path)

    groups, trailing = _group_entries(env.entries, options.group_comments)

    reverse = options.order is SortOrder.ALPHA_DESC

    def group_sort_key(grp: List[EnvEntry]) -> str:
        # Sort by the key of the kv entry in the group (last item when grouped).
        kv = next((e for e in reversed(grp) if e.key is not None), None)
        if kv is None:
            return ""
        return _sort_key(kv, options.ignore_case)

    kv_groups = [g for g in groups if any(e.key is not None for e in g)]
    comment_only_groups = [g for g in groups if all(e.key is None for e in g)]

    kv_groups.sort(key=group_sort_key, reverse=reverse)

    sorted_entries: List[EnvEntry] = []
    for grp in comment_only_groups:
        sorted_entries.extend(grp)
    for grp in kv_groups:
        sorted_entries.extend(grp)
    sorted_entries.extend(trailing)

    return EnvFile(entries=sorted_entries, path=env.path)
