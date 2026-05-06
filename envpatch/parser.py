"""Parser for .env files — handles reading and tokenizing key-value pairs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

_LINE_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$"
)
_COMMENT_RE = re.compile(r"^\s*#")
_BLANK_RE = re.compile(r"^\s*$")


@dataclass
class EnvEntry:
    """A single entry parsed from a .env file."""

    key: str
    value: str
    line_number: int
    raw: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EnvEntry):
            return NotImplemented
        return self.key == other.key and self.value == other.value


@dataclass
class EnvFile:
    """Parsed representation of a .env file."""

    path: Path
    entries: list[EnvEntry] = field(default_factory=list)
    comments: dict[int, str] = field(default_factory=dict)  # line_number -> raw line

    @property
    def as_dict(self) -> dict[str, str]:
        return {e.key: e.value for e in self.entries}

    def get(self, key: str) -> EnvEntry | None:
        for entry in self.entries:
            if entry.key == key:
                return entry
        return None


def _strip_inline_comment(value: str) -> str:
    """Remove trailing inline comments and unquote the value."""
    for quote in ('"', "'"):
        if value.startswith(quote) and value.endswith(quote) and len(value) >= 2:
            return value[1:-1]
    # strip inline comment (unquoted values)
    value = re.sub(r"\s+#.*$", "", value)
    return value.strip()


def _iter_lines(text: str) -> Iterator[tuple[int, str]]:
    for lineno, line in enumerate(text.splitlines(), start=1):
        yield lineno, line


def parse_env_text(text: str, path: Path | None = None) -> EnvFile:
    """Parse the text content of a .env file into an EnvFile object."""
    path = path or Path("<string>")
    env_file = EnvFile(path=path)

    for lineno, line in _iter_lines(text):
        if _BLANK_RE.match(line) or _COMMENT_RE.match(line):
            env_file.comments[lineno] = line
            continue
        m = _LINE_RE.match(line)
        if m:
            key = m.group("key")
            raw_value = m.group("value").strip()
            value = _strip_inline_comment(raw_value)
            env_file.entries.append(EnvEntry(key=key, value=value, line_number=lineno, raw=line))

    return env_file


def parse_env_file(path: str | Path) -> EnvFile:
    """Read and parse a .env file from disk."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    return parse_env_text(text, path=path)
