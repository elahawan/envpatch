"""Tests for envpatch.cli_normalize."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envpatch.cli_normalize import build_parser, run_normalize, run_normalize_logic
from envpatch.parser import EnvFile, EnvEntry
from envpatch.normalizer import NormalizeOptions, NormalizeResult


def make_args(**kwargs):
    defaults = {
        "file": "test.env",
        "in_place": False,
        "no_uppercase": False,
        "no_strip_whitespace": False,
        "keep_blank_duplicates": False,
        "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def make_env(*entries):
    return EnvFile(entries=list(entries), path=None)


def kv(key, value):
    return EnvEntry(key=key, value=value, comment=None, raw=f"{key}={value}")


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_parser_has_file_argument():
    parser = build_parser()
    args = parser.parse_args(["my.env"])
    assert args.file == "my.env"


def test_build_parser_dry_run_default_false():
    parser = build_parser()
    args = parser.parse_args(["my.env"])
    assert args.dry_run is False


def test_build_parser_dry_run_flag():
    parser = build_parser()
    args = parser.parse_args(["my.env", "--dry-run"])
    assert args.dry_run is True


def test_build_parser_in_place_default_false():
    parser = build_parser()
    args = parser.parse_args(["my.env"])
    assert args.in_place is False


def test_build_parser_no_uppercase_flag():
    parser = build_parser()
    args = parser.parse_args(["my.env", "--no-uppercase"])
    assert args.no_uppercase is True


def test_run_normalize_missing_file(tmp_path):
    args = make_args(file=str(tmp_path / "nonexistent.env"))
    result = run_normalize(args)
    assert result == 1


def test_run_normalize_prints_output(tmp_path, capsys):
    env_path = tmp_path / "test.env"
    env_path.write_text("db_host=localhost\n")
    args = make_args(file=str(env_path))
    run_normalize(args)
    captured = capsys.readouterr()
    assert "DB_HOST" in captured.out


def test_run_normalize_dry_run_shows_changes(tmp_path, capsys):
    env_path = tmp_path / "test.env"
    env_path.write_text("db_host=localhost\n")
    args = make_args(file=str(env_path), dry_run=True)
    run_normalize(args)
    captured = capsys.readouterr()
    assert "change" in captured.out.lower()


def test_run_normalize_in_place_writes_file(tmp_path):
    env_path = tmp_path / "test.env"
    env_path.write_text("db_host=localhost\n")
    args = make_args(file=str(env_path), in_place=True)
    run_normalize(args)
    content = env_path.read_text()
    assert "DB_HOST" in content


def test_run_normalize_logic_returns_result():
    env = make_env(kv("foo", "bar"))
    opts = NormalizeOptions()
    result = run_normalize_logic(env, opts)
    assert isinstance(result, NormalizeResult)
