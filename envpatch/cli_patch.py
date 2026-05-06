"""CLI entry point for applying a patch (merge) from a diff to a base .env file."""

import argparse
import sys
from pathlib import Path

from envpatch.parser import EnvFile
from envpatch.differ import diff_envs
from envpatch.merger import merge, ConflictStrategy
from envpatch.serializer import write_env_file
from envpatch.reporter import format_diff_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch patch",
        description="Apply changes from a patch env onto a base env file.",
    )
    parser.add_argument("base", help="Base .env file path")
    parser.add_argument("patch", help="Patch .env file path (changes to apply)")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output file path (default: overwrite base)",
    )
    parser.add_argument(
        "--strategy",
        choices=[s.value for s in ConflictStrategy],
        default=ConflictStrategy.THEIRS.value,
        help="Conflict resolution strategy (default: theirs)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without writing output",
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable colored output",
    )
    return parser


def run_patch(args: argparse.Namespace) -> int:
    base_path = Path(args.base)
    patch_path = Path(args.patch)

    if not base_path.exists():
        print(f"error: base file not found: {base_path}", file=sys.stderr)
        return 1
    if not patch_path.exists():
        print(f"error: patch file not found: {patch_path}", file=sys.stderr)
        return 1

    base_env = EnvFile.parse(base_path.read_text())
    patch_env = EnvFile.parse(patch_path.read_text())

    strategy = ConflictStrategy(args.strategy)
    diff = diff_envs(base_env, patch_env)
    result = merge(base_env, diff, strategy=strategy)

    use_color = not args.no_color
    report = format_diff_report(diff, use_color=use_color)
    print(report)

    if result.has_conflicts():
        print("warning: conflicts detected (resolved via strategy: {})".format(strategy.value), file=sys.stderr)

    if args.dry_run:
        print("[dry-run] no files written.")
        return 0

    output_path = Path(args.output) if args.output else base_path
    write_env_file(result.merged, output_path)
    print(f"written: {output_path}")
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_patch(args))


if __name__ == "__main__":
    main()
