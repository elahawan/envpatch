"""Validate .env files for common issues before patching or diffing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvFile


@dataclass
class ValidationIssue:
    line: int
    key: str | None
    message: str
    severity: str  # 'error' | 'warning'

    def __str__(self) -> str:
        loc = f"line {self.line}" if self.line else "unknown"
        key_info = f" [{self.key}]" if self.key else ""
        return f"{self.severity.upper()} ({loc}){key_info}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def validate_env_file(env: EnvFile, raw_text: str) -> ValidationResult:
    """Run validation checks on a parsed EnvFile and its raw source."""
    result = ValidationResult()
    seen_keys: dict[str, int] = {}

    for lineno, line in enumerate(raw_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            result.issues.append(ValidationIssue(
                line=lineno, key=None,
                message=f"line does not contain '=': {line!r}",
                severity="error",
            ))
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if not key:
            result.issues.append(ValidationIssue(
                line=lineno, key=None,
                message="empty key",
                severity="error",
            ))
            continue
        if key in seen_keys:
            result.issues.append(ValidationIssue(
                line=lineno, key=key,
                message=f"duplicate key (first seen on line {seen_keys[key]})",
                severity="warning",
            ))
        else:
            seen_keys[key] = lineno
        if " " in key:
            result.issues.append(ValidationIssue(
                line=lineno, key=key,
                message="key contains spaces",
                severity="warning",
            ))

    return result
