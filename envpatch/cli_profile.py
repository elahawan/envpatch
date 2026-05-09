"""CLI entry point for the `envpatch profile` sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.parser import EnvFile
from envpatch.profiler import profile_env_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch profile",
        description="Display statistics and patterns for an .env file.",
    )
    parser.add_argument("file", help="Path to the .env file to profile")
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output report as JSON",
    )
    return parser


def run_profile(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    env = EnvFile.parse(path.read_text())
    report = profile_env_file(env)

    if args.json:
        import json
        data = {
            "total_lines": report.total_lines,
            "key_count": report.key_count,
            "comment_count": report.comment_count,
            "blank_count": report.blank_count,
            "empty_value_count": report.empty_value_count,
            "sensitive_key_count": report.sensitive_key_count,
            "quoted_value_count": report.quoted_value_count,
            "duplicate_keys": report.duplicate_keys,
            "longest_key": report.longest_key,
            "longest_value_length": report.longest_value_length,
        }
        print(json.dumps(data, indent=2))
    else:
        print(report.summary())

    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_profile(args))


if __name__ == "__main__":  # pragma: no cover
    main()
