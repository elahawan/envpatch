"""Summary statistics derived from a DiffResult."""

from dataclasses import dataclass
from typing import List

from envpatch.differ import DiffResult, ChangeType


@dataclass
class DiffSummary:
    """Aggregated counts and key lists from a diff."""

    added_count: int
    removed_count: int
    changed_count: int
    unchanged_count: int
    added_keys: List[str]
    removed_keys: List[str]
    changed_keys: List[str]

    @property
    def total_changes(self) -> int:
        return self.added_count + self.removed_count + self.changed_count

    @property
    def is_identical(self) -> bool:
        return self.total_changes == 0

    def as_dict(self) -> dict:
        return {
            "added": self.added_count,
            "removed": self.removed_count,
            "changed": self.changed_count,
            "unchanged": self.unchanged_count,
            "total_changes": self.total_changes,
            "added_keys": self.added_keys,
            "removed_keys": self.removed_keys,
            "changed_keys": self.changed_keys,
        }


def summarize_diff(result: DiffResult) -> DiffSummary:
    """Build a DiffSummary from a DiffResult."""
    added_keys = [e.key for e in result.added()]
    removed_keys = [e.key for e in result.removed()]
    changed_keys = [e.key for e in result.changed()]
    unchanged_keys = [e.key for e in result.unchanged()]

    return DiffSummary(
        added_count=len(added_keys),
        removed_count=len(removed_keys),
        changed_count=len(changed_keys),
        unchanged_count=len(unchanged_keys),
        added_keys=sorted(added_keys),
        removed_keys=sorted(removed_keys),
        changed_keys=sorted(changed_keys),
    )


def format_summary(summary: DiffSummary, *, color: bool = True) -> str:
    """Return a human-readable summary string."""
    GREEN = "\033[32m" if color else ""
    RED = "\033[31m" if color else ""
    YELLOW = "\033[33m" if color else ""
    RESET = "\033[0m" if color else ""

    if summary.is_identical:
        return f"{GREEN}Files are identical.{RESET}"

    lines = ["Diff summary:"]
    if summary.added_count:
        lines.append(f"  {GREEN}+{summary.added_count} added{RESET}: {', '.join(summary.added_keys)}")
    if summary.removed_count:
        lines.append(f"  {RED}-{summary.removed_count} removed{RESET}: {', '.join(summary.removed_keys)}")
    if summary.changed_count:
        lines.append(f"  {YELLOW}~{summary.changed_count} changed{RESET}: {', '.join(summary.changed_keys)}")
    if summary.unchanged_count:
        lines.append(f"  {summary.unchanged_count} unchanged")
    return "\n".join(lines)
