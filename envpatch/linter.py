"""Linter for .env files — checks for style and best-practice issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvFile, EnvEntry


@dataclass
class LintIssue:
    line_number: int
    key: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"Line {self.line_number} [{self.code}] {self.key!r}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def errors(self, code: str | None = None) -> List[LintIssue]:
        if code is None:
            return list(self.issues)
        return [i for i in self.issues if i.code == code]


def _check_key_uppercase(entry: EnvEntry, lineno: int) -> LintIssue | None:
    if entry.key and entry.key != entry.key.upper():
        return LintIssue(
            line_number=lineno,
            key=entry.key,
            code="E001",
            message="Key should be UPPER_SNAKE_CASE",
        )
    return None


def _check_no_spaces_in_key(entry: EnvEntry, lineno: int) -> LintIssue | None:
    if entry.key and " " in entry.key:
        return LintIssue(
            line_number=lineno,
            key=entry.key,
            code="E002",
            message="Key must not contain spaces",
        )
    return None


def _check_value_not_none(entry: EnvEntry, lineno: int) -> LintIssue | None:
    if entry.key and entry.value is None:
        return LintIssue(
            line_number=lineno,
            key=entry.key,
            code="W001",
            message="Key has no value (missing '=')",
        )
    return None


def _check_no_leading_trailing_whitespace(entry: EnvEntry, lineno: int) -> LintIssue | None:
    if entry.value and entry.value != entry.value.strip():
        return LintIssue(
            line_number=lineno,
            key=entry.key,
            code="W002",
            message="Value has leading or trailing whitespace",
        )
    return None


_CHECKS = [
    _check_key_uppercase,
    _check_no_spaces_in_key,
    _check_value_not_none,
    _check_no_leading_trailing_whitespace,
]


def lint_env_file(env: EnvFile) -> LintResult:
    result = LintResult()
    for lineno, entry in enumerate(env.entries, start=1):
        if entry.is_comment or entry.key is None:
            continue
        for check in _CHECKS:
            issue = check(entry, lineno)
            if issue is not None:
                result.issues.append(issue)
    return result
