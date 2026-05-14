"""CLI entry point for filtering .env file entries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.filter import FilterOptions, filter_env_file
from envpatch.parser import EnvFile
from envpatch.serializer import serialize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch filter",
        description="Filter .env file entries by key prefix, glob pattern, or value state.",
    )
    parser.add_argument("file", help="Path to the .env file to filter")
    parser.add_argument(
        "--prefix", dest="prefixes", action="append", default=[],
        metavar="PREFIX", help="Include keys starting with PREFIX (repeatable)",
    )
    parser.add_argument(
        "--pattern", dest="patterns", action="append", default=[],
        metavar="GLOB", help="Include keys matching GLOB pattern (repeatable)",
    )
    parser.add_argument(
        "--exclude-prefix", dest="exclude_prefixes", action="append", default=[],
        metavar="PREFIX", help="Exclude keys starting with PREFIX (repeatable)",
    )
    parser.add_argument(
        "--exclude-pattern", dest="exclude_patterns", action="append", default=[],
        metavar="GLOB", help="Exclude keys matching GLOB pattern (repeatable)",
    )
    parser.add_argument(
        "--only-empty", action="store_true", default=False,
        help="Only include keys with empty values",
    )
    parser.add_argument(
        "--only-nonempty", action="store_true", default=False,
        help="Only include keys with non-empty values",
    )
    parser.add_argument(
        "--show-excluded", action="store_true", default=False,
        help="Print excluded entries instead of matched entries",
    )
    return parser


def run_filter(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=err)
        return 1

    try:
        env = EnvFile.parse(path.read_text())
    except Exception as exc:  # pragma: no cover
        print(f"error: failed to parse {path}: {exc}", file=err)
        return 1

    opts = FilterOptions(
        prefixes=args.prefixes,
        patterns=args.patterns,
        exclude_prefixes=args.exclude_prefixes,
        exclude_patterns=args.exclude_patterns,
        only_empty=args.only_empty,
        only_nonempty=args.only_nonempty,
    )

    result = filter_env_file(env, opts)
    target = result.excluded if args.show_excluded else result.matched
    print(serialize(target), end="", file=out)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_filter(args))
