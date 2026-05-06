"""Audit log for tracking merge and patch operations applied to .env files."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class AuditEntry:
    timestamp: str
    operation: str  # 'merge' | 'patch' | 'diff'
    base_file: str
    other_file: Optional[str]
    keys_added: List[str] = field(default_factory=list)
    keys_removed: List[str] = field(default_factory=list)
    keys_changed: List[str] = field(default_factory=list)
    keys_conflicted: List[str] = field(default_factory=list)
    strategy: Optional[str] = None
    dry_run: bool = False

    def summary(self) -> str:
        parts = [
            f"[{self.timestamp}] {self.operation.upper()} {self.base_file}",
        ]
        if self.other_file:
            parts[0] += f" <- {self.other_file}"
        if self.strategy:
            parts.append(f"  strategy={self.strategy}")
        if self.dry_run:
            parts.append("  (dry-run)")
        for label, keys in [
            ("added", self.keys_added),
            ("removed", self.keys_removed),
            ("changed", self.keys_changed),
            ("conflicted", self.keys_conflicted),
        ]:
            if keys:
                parts.append(f"  {label}: {', '.join(keys)}")
        return "\n".join(parts)


def create_entry(
    operation: str,
    base_file: str,
    other_file: Optional[str] = None,
    keys_added: Optional[List[str]] = None,
    keys_removed: Optional[List[str]] = None,
    keys_changed: Optional[List[str]] = None,
    keys_conflicted: Optional[List[str]] = None,
    strategy: Optional[str] = None,
    dry_run: bool = False,
) -> AuditEntry:
    return AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        operation=operation,
        base_file=base_file,
        other_file=other_file,
        keys_added=keys_added or [],
        keys_removed=keys_removed or [],
        keys_changed=keys_changed or [],
        keys_conflicted=keys_conflicted or [],
        strategy=strategy,
        dry_run=dry_run,
    )


def append_to_log(entry: AuditEntry, log_path: str) -> None:
    """Append a single audit entry as a JSON line to *log_path*."""
    os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry)) + "\n")


def load_log(log_path: str) -> List[AuditEntry]:
    """Read all audit entries from *log_path*. Returns empty list if missing."""
    if not os.path.exists(log_path):
        return []
    entries: List[AuditEntry] = []
    with open(log_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                data = json.loads(line)
                entries.append(AuditEntry(**data))
    return entries
