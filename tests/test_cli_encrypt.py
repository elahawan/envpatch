"""Tests for envpatch.cli_encrypt."""

import argparse
import os
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("cryptography", reason="cryptography package required")

from envpatch.cli_encrypt import build_parser, run_encrypt
from envpatch.encryptor import generate_key


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "command": "encrypt",
        "file": ".env",
        "key": None,
        "all_keys": False,
        "output": None,
        "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_parser_has_encrypt_subcommand():
    parser = build_parser()
    args = parser.parse_args(["encrypt", "my.env", "--key", "abc"])
    assert args.command == "encrypt"
    assert args.file == "my.env"


def test_build_parser_has_decrypt_subcommand():
    parser = build_parser()
    args = parser.parse_args(["decrypt", "my.env", "--key", "abc"])
    assert args.command == "decrypt"


def test_build_parser_generate_key_subcommand():
    parser = build_parser()
    args = parser.parse_args(["generate-key"])
    assert args.command == "generate-key"


def test_build_parser_dry_run_flag():
    parser = build_parser()
    args = parser.parse_args(["encrypt", "my.env", "--key", "k", "--dry-run"])
    assert args.dry_run is True


def test_run_encrypt_generate_key_prints_key(capsys):
    args = argparse.Namespace(command="generate-key")
    result = run_encrypt(args)
    captured = capsys.readouterr()
    assert result == 0
    assert len(captured.out.strip()) > 0


def test_run_encrypt_missing_file_returns_1(tmp_path):
    args = make_args(file=str(tmp_path / "nonexistent.env"), key=generate_key())
    result = run_encrypt(args)
    assert result == 1


def test_run_encrypt_dry_run_prints_output(tmp_path, capsys):
    env_path = tmp_path / ".env"
    env_path.write_text("DB_PASSWORD=secret\nAPP_NAME=myapp\n")
    key = generate_key()
    args = make_args(file=str(env_path), key=key, dry_run=True)
    result = run_encrypt(args)
    captured = capsys.readouterr()
    assert result == 0
    assert "APP_NAME" in captured.out or "DB_PASSWORD" in captured.out


def test_run_encrypt_writes_output_file(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("DB_PASSWORD=secret\n")
    out_path = tmp_path / "encrypted.env"
    key = generate_key()
    args = make_args(file=str(env_path), key=key, output=str(out_path))
    result = run_encrypt(args)
    assert result == 0
    assert out_path.exists()
    assert "secret" not in out_path.read_text()


def test_run_decrypt_roundtrip(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("DB_PASSWORD=secret123\n")
    key = generate_key()
    enc_args = make_args(file=str(env_path), key=key)
    run_encrypt(enc_args)
    dec_args = make_args(command="decrypt", file=str(env_path), key=key)
    result = run_encrypt(dec_args)
    assert result == 0
    assert "secret123" in env_path.read_text()
