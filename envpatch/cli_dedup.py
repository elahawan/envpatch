"""CLI entry point for the deduplication command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.parser import EnvFile
from envpatch.deduplicator import deduplicate_env_file
from envpatch.serializer import serialize, write_env_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch dedup",
        description="Remove duplicate keys from an .env file.",
    )
    parser.add_argument("file", help="Path to the .env file to deduplicate.")
    parser.add_argument(
        "--keep",
        choices=["first", "last"],
        default="last",
        help="Which occurrence to keep when a duplicate is found (default: last).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print the result without writing back to disk.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress informational output.",
    )
    return parser


def run_dedup(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    env = EnvFile.parse(path.read_text())
    result = deduplicate_env_file(env, keep=args.keep)

    if not args.quiet:
        if result.was_modified:
            for key, indices in result.duplicates.items():
                print(
                    f"  duplicate: {key!r} — removed {len(indices)} extra occurrence(s)"
                )
        else:
            print("No duplicates found.")

    if args.dry_run:
        print(serialize(result.as_env_file()))
        return 0

    if result.was_modified:
        write_env_file(result.as_env_file(), path)
        if not args.quiet:
            print(f"Written: {path}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_dedup(args))


if __name__ == "__main__":  # pragma: no cover
    main()
