"""CLI entry point for the normalize command."""

import argparse
import sys
from pathlib import Path

from envpatch.parser import EnvFile
from envpatch.normalizer import NormalizeOptions, normalize_env_file
from envpatch.serializer import serialize, write_env_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch normalize",
        description="Normalize a .env file: uppercase keys, strip whitespace, remove duplicate blank lines.",
    )
    parser.add_argument("file", help="Path to the .env file to normalize")
    parser.add_argument(
        "--in-place", action="store_true", help="Overwrite the input file with normalized output"
    )
    parser.add_argument(
        "--no-uppercase", action="store_true", help="Do not uppercase keys"
    )
    parser.add_argument(
        "--no-strip-whitespace", action="store_true", help="Do not strip trailing whitespace from values"
    )
    parser.add_argument(
        "--keep-blank-duplicates", action="store_true", help="Preserve duplicate blank lines"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without writing output"
    )
    return parser


def run_normalize(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    env_file = EnvFile.from_path(str(path))

    options = NormalizeOptions(
        uppercase_keys=not args.no_uppercase,
        strip_trailing_whitespace=not args.no_strip_whitespace,
        remove_blank_duplicates=not args.keep_blank_duplicates,
    )

    result = run_normalize_logic(env_file, options)

    if args.dry_run:
        for change in result.changes:
            print(f"  ~ {change}")
        print(f"\n{result.change_count} change(s) would be applied.")
        return 0

    if args.in_place:
        write_env_file(result.normalized, str(path))
        print(f"Normalized {path} ({result.change_count} change(s) applied).")
    else:
        print(serialize(result.normalized), end="")

    return 0


def run_normalize_logic(env_file, options):
    return normalize_env_file(env_file, options)


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_normalize(args))


if __name__ == "__main__":
    main()
