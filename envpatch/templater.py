"""Template generation from .env files — produce .env.example with values redacted."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envpatch.parser import EnvFile, EnvEntry


@dataclass
class TemplateOptions:
    placeholder: str = "<value>"
    preserve_comments: bool = True
    preserve_blank_lines: bool = True
    redact_pattern: Optional[str] = None  # regex; if set, only matching keys are redacted


def generate_template(env_file: EnvFile, options: Optional[TemplateOptions] = None) -> EnvFile:
    """Return a new EnvFile with all key values replaced by a placeholder."""
    if options is None:
        options = TemplateOptions()

    import re

    pattern = re.compile(options.redact_pattern) if options.redact_pattern else None

    new_entries: list[EnvEntry] = []
    for entry in env_file.entries:
        if entry.key is None:
            # comment or blank line
            if entry.raw.strip() == "" and not options.preserve_blank_lines:
                continue
            if entry.raw.strip().startswith("#") and not options.preserve_comments:
                continue
            new_entries.append(entry)
            continue

        if pattern is not None and not pattern.search(entry.key):
            # key does not match redact pattern — keep original value
            new_entries.append(entry)
        else:
            redacted = EnvEntry(
                key=entry.key,
                value=options.placeholder,
                raw=f"{entry.key}={options.placeholder}",
                comment=entry.comment,
            )
            new_entries.append(redacted)

    return EnvFile(entries=new_entries, path=None)


def template_from_path(src_path: str, options: Optional[TemplateOptions] = None) -> EnvFile:
    """Parse *src_path* and return a redacted template EnvFile."""
    from envpatch.parser import parse_env_file

    env = parse_env_file(src_path)
    return generate_template(env, options)


def write_template(src_path: str, dest_path: str, options: Optional[TemplateOptions] = None) -> None:
    """Generate a redacted template from *src_path* and write it to *dest_path*.

    Args:
        src_path: Path to the source .env file to read and redact.
        dest_path: Path where the rendered template will be written.
        options: Optional :class:`TemplateOptions` controlling redaction behaviour.
    """
    template = template_from_path(src_path, options)
    lines = [entry.raw for entry in template.entries]
    with open(dest_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
        if lines:
            fh.write("\n")
