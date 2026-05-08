"""CLI entry point for encrypting/decrypting .env files."""

from __future__ import annotations

import argparse
import os
import sys

from envpatch.encryptor import decrypt_env_file, encrypt_env_file, generate_key
from envpatch.parser import EnvFile
from envpatch.serializer import serialize, write_env_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch-encrypt",
        description="Encrypt or decrypt sensitive values in a .env file.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encrypt", help="Encrypt sensitive values")
    enc.add_argument("file", help="Path to .env file")
    enc.add_argument("--key", help="Fernet key (or set ENVPATCH_KEY env var)")
    enc.add_argument("--all", dest="all_keys", action="store_true", help="Encrypt all keys, not just sensitive ones")
    enc.add_argument("--output", "-o", help="Output file (default: overwrite input)")
    enc.add_argument("--dry-run", action="store_true", help="Print result without writing")

    dec = sub.add_parser("decrypt", help="Decrypt encrypted values")
    dec.add_argument("file", help="Path to .env file")
    dec.add_argument("--key", help="Fernet key (or set ENVPATCH_KEY env var)")
    dec.add_argument("--all", dest="all_keys", action="store_true")
    dec.add_argument("--output", "-o", help="Output file (default: overwrite input)")
    dec.add_argument("--dry-run", action="store_true")

    sub.add_parser("generate-key", help="Generate a new encryption key")

    return parser


def _resolve_key(args: argparse.Namespace) -> str:
    key = getattr(args, "key", None) or os.environ.get("ENVPATCH_KEY", "")
    if not key:
        print("Error: encryption key required (--key or ENVPATCH_KEY)", file=sys.stderr)
        sys.exit(1)
    return key


def run_encrypt(args: argparse.Namespace) -> int:
    if args.command == "generate-key":
        print(generate_key())
        return 0

    if not os.path.exists(args.file):
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    key = _resolve_key(args)
    env_file = EnvFile.parse(open(args.file).read())
    sensitive_only = not args.all_keys

    if args.command == "encrypt":
        result = encrypt_env_file(env_file, key, sensitive_only=sensitive_only)
        verb = "Encrypted"
    else:
        result = decrypt_env_file(env_file, key, sensitive_only=sensitive_only)
        verb = "Decrypted"

    output_text = serialize(result.as_env_file)

    if args.dry_run:
        print(output_text)
    else:
        out_path = args.output or args.file
        write_env_file(result.as_env_file, out_path)

    if result.failed_keys:
        print(f"Warning: failed to process keys: {', '.join(result.failed_keys)}", file=sys.stderr)

    print(f"{verb} {len(result.encrypted_keys)} key(s): {', '.join(result.encrypted_keys)}")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_encrypt(args))
