"""Export EnvFile contents to various formats (JSON, YAML, shell script)."""

from __future__ import annotations

import json
from enum import Enum
from typing import Optional

from envpatch.parser import EnvFile


class ExportFormat(str, Enum):
    JSON = "json"
    YAML = "yaml"
    SHELL = "shell"


def export_as_json(env: EnvFile, indent: int = 2) -> str:
    """Serialize an EnvFile to a JSON string."""
    data = {entry.key: entry.value for entry in env.entries if entry.key is not None}
    return json.dumps(data, indent=indent)


def export_as_yaml(env: EnvFile) -> str:
    """Serialize an EnvFile to a YAML-compatible string (no external deps)."""
    lines: list[str] = []
    for entry in env.entries:
        if entry.key is None:
            continue
        value = entry.value if entry.value is not None else ""
        # Minimal quoting: wrap in double quotes if value contains special chars
        if any(c in value for c in (":", "#", "{", "}", "[", "]", ",", "&", "*")):
            value = f'"{value}"'
        lines.append(f"{entry.key}: {value}")
    return "\n".join(lines)


def export_as_shell(env: EnvFile) -> str:
    """Serialize an EnvFile as export statements for shell sourcing."""
    lines: list[str] = ["#!/usr/bin/env sh"]
    for entry in env.entries:
        if entry.key is None:
            continue
        value = entry.value if entry.value is not None else ""
        escaped = value.replace("'", "'\"'\"'")
        lines.append(f"export {entry.key}='{escaped}'")
    return "\n".join(lines)


def export_env(env: EnvFile, fmt: ExportFormat) -> str:
    """Dispatch export to the appropriate formatter."""
    if fmt == ExportFormat.JSON:
        return export_as_json(env)
    if fmt == ExportFormat.YAML:
        return export_as_yaml(env)
    if fmt == ExportFormat.SHELL:
        return export_as_shell(env)
    raise ValueError(f"Unsupported export format: {fmt}")
