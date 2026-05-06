"""Human-readable diff report generation for envpatch."""

from typing import TextIO
import sys

from envpatch.differ import ChangeType, DiffResult


ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def format_diff_report(result: DiffResult, use_color: bool = True) -> str:
    """Format a DiffResult into a human-readable string report."""
    lines = []

    if result.is_identical:
        lines.append("No differences found.")
        return "\n".join(lines)

    summary_parts = []
    if result.added:
        summary_parts.append(f"{len(result.added)} added")
    if result.removed:
        summary_parts.append(f"{len(result.removed)} removed")
    if result.changed:
        summary_parts.append(f"{len(result.changed)} changed")

    header = f"Diff summary: {', '.join(summary_parts)}"
    lines.append(_colorize(header, ANSI_BOLD, use_color))
    lines.append("")

    for entry in result.added:
        line = f"+ {entry.key}={entry.new_value}"
        lines.append(_colorize(line, ANSI_GREEN, use_color))

    for entry in result.removed:
        line = f"- {entry.key}={entry.old_value}"
        lines.append(_colorize(line, ANSI_RED, use_color))

    for entry in result.changed:
        old_line = f"- {entry.key}={entry.old_value}"
        new_line = f"+ {entry.key}={entry.new_value}"
        lines.append(_colorize(old_line, ANSI_RED, use_color))
        lines.append(_colorize(new_line, ANSI_GREEN, use_color))

    return "\n".join(lines)


def print_diff_report(
    result: DiffResult,
    stream: TextIO = sys.stdout,
    use_color: bool = True,
) -> None:
    """Print a formatted diff report to the given stream."""
    report = format_diff_report(result, use_color=use_color)
    print(report, file=stream)
