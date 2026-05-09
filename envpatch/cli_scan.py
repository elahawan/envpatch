"""CLI entry point for the `envpatch scan` command."""

from __future__ import annotations

import argparse
import sys

from envpatch.parser import EnvFile
from envpatch.scanner import scan_env_file, ScanSeverity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch scan",
        description="Scan a .env file for security and hygiene issues.",
    )
    parser.add_argument("file", help="Path to the .env file to scan")
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with non-zero status on warnings as well as errors",
    )
    return parser


def _colorize(text: str, color: str, use_color: bool) -> str:
    codes = {"red": "\033[31m", "yellow": "\033[33m", "reset": "\033[0m"}
    if not use_color:
        return text
    return f"{codes.get(color, '')}{text}{codes['reset']}"


def run_scan(args: argparse.Namespace) -> int:
    try:
        env = EnvFile.from_path(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 2

    report = scan_env_file(env)
    use_color = not args.no_color

    if report.is_clean:
        print("No issues found.")
        return 0

    for issue in report.issues:
        color = "red" if issue.severity == ScanSeverity.ERROR else "yellow"
        print(_colorize(str(issue), color, use_color))

    print()
    print(report.summary())

    has_errors = len(report.errors) > 0
    has_warnings = len(report.warnings) > 0

    if has_errors:
        return 1
    if args.strict and has_warnings:
        return 1
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_scan(args))


if __name__ == "__main__":
    main()
