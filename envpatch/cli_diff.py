"""CLI entry point for the envpatch diff command."""

import argparse
import sys

from envpatch.parser import EnvFile
from envpatch.differ import diff_env_files
from envpatch.reporter import print_diff_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch-diff",
        description="Show differences between two .env files.",
    )
    parser.add_argument("base", help="Base .env file (original)")
    parser.add_argument("other", help="Other .env file (modified)")
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if files differ (like diff(1))",
    )
    return parser


def run_diff(args: argparse.Namespace) -> int:
    try:
        base_env = EnvFile.parse(open(args.base).read())
    except FileNotFoundError:
        print(f"Error: base file not found: {args.base}", file=sys.stderr)
        return 2

    try:
        other_env = EnvFile.parse(open(args.other).read())
    except FileNotFoundError:
        print(f"Error: other file not found: {args.other}", file=sys.stderr)
        return 2

    result = diff_env_files(base_env, other_env)
    use_color = not args.no_color and sys.stdout.isatty()
    print_diff_report(result, stream=sys.stdout, use_color=use_color)

    if args.exit_code and not result.is_identical:
        return 1
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_diff(args))


if __name__ == "__main__":
    main()
