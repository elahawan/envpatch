"""Inject values from an EnvFile into the current process environment or a subprocess."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from envpatch.parser import EnvFile


@dataclass
class InjectResult:
    """Result of an injection operation."""
    injected: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)

    @property
    def inject_count(self) -> int:
        return len(self.injected)

    @property
    def skip_count(self) -> int:
        return len(self.skipped)

    def was_skipped(self, key: str) -> bool:
        return key in self.skipped


def inject_into_environ(
    env_file: EnvFile,
    *,
    overwrite: bool = False,
    prefix: Optional[str] = None,
) -> InjectResult:
    """Inject key/value pairs from *env_file* into ``os.environ``.

    Args:
        env_file: Parsed env file to inject from.
        overwrite: If False (default), existing environment variables are not
            overwritten and the key is recorded as skipped.
        prefix: Optional string prefix to prepend to every key before injecting.
    """
    result = InjectResult()
    for entry in env_file.entries:
        if entry.key is None or entry.value is None:
            continue
        target_key = f"{prefix}{entry.key}" if prefix else entry.key
        if not overwrite and target_key in os.environ:
            result.skipped.append(target_key)
            continue
        os.environ[target_key] = entry.value
        result.injected[target_key] = entry.value
    return result


def run_with_env(
    cmd: Sequence[str],
    env_file: EnvFile,
    *,
    overwrite: bool = True,
    prefix: Optional[str] = None,
    extra_env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    """Run *cmd* as a subprocess with variables from *env_file* merged into the
    environment.

    The host process environment is used as the base; values from *env_file*
    are layered on top (subject to *overwrite*).
    """
    merged = dict(os.environ)
    for entry in env_file.entries:
        if entry.key is None or entry.value is None:
            continue
        target_key = f"{prefix}{entry.key}" if prefix else entry.key
        if not overwrite and target_key in merged:
            continue
        merged[target_key] = entry.value
    if extra_env:
        merged.update(extra_env)
    return subprocess.run(list(cmd), env=merged)  # noqa: S603
