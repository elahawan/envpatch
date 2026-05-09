"""Profile an .env file: summarise key statistics and patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvFile, EnvEntry
from envpatch.redactor import _is_sensitive


@dataclass
class ProfileReport:
    total_lines: int = 0
    key_count: int = 0
    comment_count: int = 0
    blank_count: int = 0
    empty_value_count: int = 0
    sensitive_key_count: int = 0
    quoted_value_count: int = 0
    duplicate_keys: List[str] = field(default_factory=list)
    longest_key: str = ""
    longest_value_length: int = 0

    def summary(self) -> str:
        lines = [
            f"Total lines      : {self.total_lines}",
            f"Keys             : {self.key_count}",
            f"Comments         : {self.comment_count}",
            f"Blank lines      : {self.blank_count}",
            f"Empty values     : {self.empty_value_count}",
            f"Sensitive keys   : {self.sensitive_key_count}",
            f"Quoted values    : {self.quoted_value_count}",
            f"Duplicate keys   : {len(self.duplicate_keys)}",
            f"Longest key      : {self.longest_key!r}",
            f"Longest value len: {self.longest_value_length}",
        ]
        if self.duplicate_keys:
            lines.append(f"  Duplicates: {', '.join(self.duplicate_keys)}")
        return "\n".join(lines)


def profile_env_file(env: EnvFile) -> ProfileReport:
    report = ProfileReport(total_lines=len(env.entries))
    seen_keys: dict[str, int] = {}

    for entry in env.entries:
        if entry.key is None:
            if entry.raw.strip() == "" or entry.raw.strip() == "\n":
                report.blank_count += 1
            else:
                report.comment_count += 1
            continue

        report.key_count += 1
        seen_keys[entry.key] = seen_keys.get(entry.key, 0) + 1

        value = entry.value or ""

        if not value:
            report.empty_value_count += 1

        if _is_sensitive(entry.key):
            report.sensitive_key_count += 1

        raw_val = entry.raw
        eq_pos = raw_val.find("=")
        if eq_pos != -1:
            raw_rhs = raw_val[eq_pos + 1:].strip().split("#")[0].strip()
            if (raw_rhs.startswith('"') and raw_rhs.endswith('"')) or \
               (raw_rhs.startswith("'") and raw_rhs.endswith("'")):
                report.quoted_value_count += 1

        if len(entry.key) > len(report.longest_key):
            report.longest_key = entry.key

        if len(value) > report.longest_value_length:
            report.longest_value_length = len(value)

    report.duplicate_keys = [k for k, count in seen_keys.items() if count > 1]
    return report
