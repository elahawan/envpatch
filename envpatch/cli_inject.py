"""CLI entry-point for the ``envpatch inject`` command.

Usage examples::

    envpatch inject .env -- python manage.py runserver
    envpatch inject .env --prefix APP_ --overwrite -- printenv
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from envpatch.parser import EnvFile
from envpatch.injector import run_with_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch inject",
        description="Run a command with variables from an .env file injected.",
    )
    parser.add_argument(
        "file",
        metavar="FILE",
        help="Path to the .env file to inject.",
    )
    parser.add_argument(
        "cmd",
        metavar="CMD",
        nargs=argparse.REMAINDER,
        help="Command to run (use -- to separate from envpatch flags).",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        metavar="PREFIX",
        help="Prepend PREFIX to every injected key.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing environment variables (default: skip).",
    )
    return parser


def run_inject(
    args: argparse.Namespace,
    argv: Optional[Sequence[str]] = None,
) -> int:
    try:
        env_file = EnvFile.parse_file(args.file)
    except FileNotFoundError:
        print(f"envpatch inject: file not found: {args.file}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"envpatch inject: failed to parse {args.file}: {exc}", file=sys.stderr)
        return 1

    cmd: List[str] = [a for a in (args.cmd or []) if a != "--"]
    if not cmd:
        print("envpatch inject: no command specified.", file=sys.stderr)
        return 1

    proc = run_with_env(
        cmd,
        env_file,
        overwrite=args.overwrite,
        prefix=args.prefix,
    )
    return proc.returncode


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_inject(args))


if __name__ == "__main__":  # pragma: no cover
    main()
