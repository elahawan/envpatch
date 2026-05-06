"""Serialize EnvFile back to .env file string format."""

from typing import Optional
from envpatch.parser import EnvFile, EnvEntry


def serialize(env_file: EnvFile, quote_values: bool = False) -> str:
    """Convert an EnvFile back to a .env formatted string."""
    lines = []
    for entry in env_file.entries:
        line = _serialize_entry(entry, quote_values=quote_values)
        lines.append(line)
    return "\n".join(lines)


def _serialize_entry(entry: EnvEntry, quote_values: bool = False) -> str:
    if entry.key is None:
        # Blank line or comment-only line
        return entry.comment if entry.comment else ""

    value = entry.value if entry.value is not None else ""

    if quote_values or _needs_quoting(value):
        value = _quote(value)

    base = f"{entry.key}={value}"

    if entry.comment:
        base = f"{base}  {entry.comment}"

    return base


def _needs_quoting(value: str) -> bool:
    """Return True if the value contains spaces or special characters."""
    return any(c in value for c in (" ", "\t", "#", "'", '"'))


def _quote(value: str) -> str:
    """Wrap value in double quotes, escaping internal double quotes."""
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def write_env_file(env_file: EnvFile, path: str, quote_values: bool = False) -> None:
    """Write an EnvFile to disk at the given path."""
    content = serialize(env_file, quote_values=quote_values)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        if not content.endswith("\n"):
            f.write("\n")
