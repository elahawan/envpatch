"""CLI entry point for the diff-summary subcommand."""

import argparse
import json
import sys

from envpatch.parser import EnvFile
from envpatch.differ import diff_env_files
from envpatch.differ_summary import summarize_diff, format_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch diff-summary",
        description="Print a summary of differences between two .env files.",
    )
    parser.add_argument("base", help="Base .env file")
    parser.add_argument("other", help="Other .env file to compare against base")
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        default=False,
        help="Output summary as JSON",
    )
    parser.add_argument(
        "--no-color",
        dest="no_color",
        action="store_true",
        default=False,
        help="Disable colored output",
    )
    parser.add_argument(
        "--exit-code",
        dest="exit_code",
        action="store_true",
        default=False,
        help="Exit with code 1 if files differ",
    )
    return parser


def run_summary(args: argparse.Namespace) -> int:
    try:
        base = EnvFile.parse(open(args.base).read())
    except FileNotFoundError:
        print(f"error: base file not found: {args.base}", file=sys.stderr)
        return 2

    try:
        other = EnvFile.parse(open(args.other).read())
    except FileNotFoundError:
        print(f"error: other file not found: {args.other}", file=sys.stderr)
        return 2

    result = diff_env_files(base, other)
    summary = summarize_diff(result)

    if args.as_json:
        print(json.dumps(summary.as_dict(), indent=2))
    else:
        print(format_summary(summary, color=not args.no_color))

    if args.exit_code and not summary.is_identical:
        return 1
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_summary(args))


if __name__ == "__main__":
    main()
