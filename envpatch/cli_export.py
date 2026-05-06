"""CLI entry point for exporting .env files to other formats."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envpatch.exporter import ExportFormat, export_env
from envpatch.parser import EnvFile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch-export",
        description="Export a .env file to JSON, YAML, or shell format.",
    )
    parser.add_argument("file", help="Path to the .env file to export")
    parser.add_argument(
        "--format",
        "-f",
        choices=[f.value for f in ExportFormat],
        default=ExportFormat.JSON.value,
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write output to this file instead of stdout",
    )
    return parser


def run_export(args: argparse.Namespace) -> int:
    source = Path(args.file)
    if not source.exists():
        print(f"error: file not found: {source}", file=sys.stderr)
        return 1

    try:
        env = EnvFile.parse(source.read_text())
    except Exception as exc:  # noqa: BLE001
        print(f"error: failed to parse {source}: {exc}", file=sys.stderr)
        return 1

    fmt = ExportFormat(args.format)
    output = export_env(env, fmt)

    if args.output:
        Path(args.output).write_text(output)
    else:
        print(output)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_export(args))


if __name__ == "__main__":  # pragma: no cover
    main()
