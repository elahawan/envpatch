"""CLI entry point for the merge subcommand."""

import sys
import argparse
from typing import Optional

from envpatch.parser import EnvFile
from envpatch.differ import diff
from envpatch.merger import merge, ConflictStrategy
from envpatch.serializer import serialize, write_env_file


def build_parser(parent: Optional[argparse.ArgumentParser] = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="envpatch merge",
        description="Merge changes from a target .env into a base .env file.",
    )
    parser.add_argument("base", help="Path to the base .env file")
    parser.add_argument("target", help="Path to the target .env file with desired changes")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (default: overwrite base)",
    )
    parser.add_argument(
        "--strategy", "-s",
        choices=[s.value for s in ConflictStrategy],
        default=ConflictStrategy.THEIRS.value,
        help="Conflict resolution strategy (default: theirs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print merged output without writing to disk",
    )
    parser.add_argument(
        "--quote",
        action="store_true",
        help="Quote all values in output",
    )
    return parser


def run_merge(args: argparse.Namespace) -> int:
    try:
        base_env = EnvFile.from_file(args.base)
    except FileNotFoundError:
        print(f"Error: base file not found: {args.base}", file=sys.stderr)
        return 1

    try:
        target_env = EnvFile.from_file(args.target)
    except FileNotFoundError:
        print(f"Error: target file not found: {args.target}", file=sys.stderr)
        return 1

    strategy = ConflictStrategy(args.strategy)
    diff_result = diff(base_env, target_env)
    result = merge(base_env, diff_result, strategy=strategy)

    if result.conflicts:
        print(f"Resolved {len(result.conflicts)} conflict(s) using strategy '{strategy.value}':")
        for c in result.conflicts:
            print(f"  {c.key}: '{c.base_value}' -> '{c.resolved_value}'")

    print(f"Applied {len(result.applied)} change(s), skipped {len(result.skipped)}.")

    output = serialize(result.merged, quote_values=args.quote)

    if args.dry_run:
        print("\n--- Merged Output ---")
        print(output)
        return 0

    out_path = args.output or args.base
    write_env_file(result.merged, out_path, quote_values=args.quote)
    print(f"Merged file written to: {out_path}")
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_merge(args))


if __name__ == "__main__":
    main()
