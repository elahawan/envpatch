"""Interactive conflict resolution prompt for use in CLI tools."""

from __future__ import annotations

from typing import List

from envpatch.merger import MergeConflict, ConflictStrategy
from envpatch.differ import ChangeType


PROMPT_TEMPLATE = """
Conflict on key: {key}
  [o] ours   = {ours}
  [t] theirs = {theirs}
Choose [o/t/s(kip)]: """


def _prompt_choice(key: str, ours: str | None, theirs: str | None) -> str | None:
    """Prompt user to resolve a single conflict. Returns chosen value or None to skip."""
    prompt = PROMPT_TEMPLATE.format(
        key=key,
        ours=repr(ours),
        theirs=repr(theirs),
    )
    while True:
        try:
            choice = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if choice in ("o", "ours"):
            return ours
        if choice in ("t", "theirs"):
            return theirs
        if choice in ("s", "skip"):
            return None
        print("  Invalid choice. Enter o, t, or s.")


def resolve_conflicts_interactively(
    conflicts: List[MergeConflict],
) -> dict[str, str | None]:
    """
    Walk through each conflict and prompt the user to pick a resolution.

    Returns a mapping of key -> chosen value (None means skip / keep ours).
    """
    resolutions: dict[str, str | None] = {}
    total = len(conflicts)
    for idx, conflict in enumerate(conflicts, start=1):
        print(f"\n[{idx}/{total}] Resolving conflict...")
        chosen = _prompt_choice(
            key=conflict.key,
            ours=conflict.ours_value,
            theirs=conflict.theirs_value,
        )
        resolutions[conflict.key] = chosen
    return resolutions


def apply_interactive_resolutions(
    base_dict: dict[str, str | None],
    resolutions: dict[str, str | None],
) -> dict[str, str | None]:
    """Apply user-chosen resolutions onto a base dict, returning updated dict."""
    result = dict(base_dict)
    for key, value in resolutions.items():
        if value is None:
            # skip — keep whatever is in base
            continue
        result[key] = value
    return result
