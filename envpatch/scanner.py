"""Scanner: detect common security and hygiene issues in .env files."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from envpatch.parser import EnvFile, EnvEntry


class ScanSeverity(Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ScanIssue:
    key: str
    code: str
    message: str
    severity: ScanSeverity

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.code}: {self.key} — {self.message}"


@dataclass
class ScanReport:
    issues: List[ScanIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def errors(self) -> List[ScanIssue]:
        return [i for i in self.issues if i.severity == ScanSeverity.ERROR]

    @property
    def warnings(self) -> List[ScanIssue]:
        return [i for i in self.issues if i.severity == ScanSeverity.WARNING]

    def summary(self) -> str:
        return (
            f"{len(self.errors)} error(s), {len(self.warnings)} warning(s) "
            f"across {len(self.issues)} total issue(s)"
        )


_PLACEHOLDER_VALUES = {"changeme", "todo", "fixme", "placeholder", "example", "xxx", "your_value_here"}
_SENSITIVE_PATTERNS = ("password", "secret", "token", "api_key", "private_key", "auth")


def _is_sensitive_key(key: str) -> bool:
    lower = key.lower()
    return any(pat in lower for pat in _SENSITIVE_PATTERNS)


def _check_entry(entry: EnvEntry) -> List[ScanIssue]:
    issues: List[ScanIssue] = []
    key = entry.key
    value = entry.value or ""

    if _is_sensitive_key(key) and value.strip().lower() in _PLACEHOLDER_VALUES:
        issues.append(ScanIssue(
            key=key,
            code="S001",
            message="Sensitive key contains a placeholder value",
            severity=ScanSeverity.ERROR,
        ))

    if _is_sensitive_key(key) and value == "":
        issues.append(ScanIssue(
            key=key,
            code="S002",
            message="Sensitive key has an empty value",
            severity=ScanSeverity.WARNING,
        ))

    if len(value) > 0 and value == value.strip() and "  " in value:
        issues.append(ScanIssue(
            key=key,
            code="S003",
            message="Value contains consecutive whitespace",
            severity=ScanSeverity.WARNING,
        ))

    return issues


def scan_env_file(env: EnvFile) -> ScanReport:
    """Scan an EnvFile for security and hygiene issues."""
    report = ScanReport()
    for entry in env.entries:
        if entry.key is None:
            continue
        report.issues.extend(_check_entry(entry))
    return report
