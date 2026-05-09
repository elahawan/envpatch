"""Tests for envpatch.cli_profile."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from envpatch.cli_profile import build_parser, run_profile


def make_args(**kwargs) -> SimpleNamespace:
    defaults = {"file": "test.env", "json": False}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None


def test_build_parser_has_file_argument():
    parser = build_parser()
    args = parser.parse_args(["myfile.env"])
    assert args.file == "myfile.env"


def test_build_parser_json_flag_default_false():
    parser = build_parser()
    args = parser.parse_args(["myfile.env"])
    assert args.json is False


def test_build_parser_json_flag_set():
    parser = build_parser()
    args = parser.parse_args(["myfile.env", "--json"])
    assert args.json is True


def test_run_profile_missing_file(tmp_path):
    args = make_args(file=str(tmp_path / "nonexistent.env"))
    result = run_profile(args)
    assert result == 1


def test_run_profile_returns_zero_on_success(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("HOST=localhost\nPORT=5432\n")
    args = make_args(file=str(env_file))
    result = run_profile(args)
    assert result == 0


def test_run_profile_text_output_contains_keys(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("HOST=localhost\nPORT=5432\n")
    args = make_args(file=str(env_file))
    run_profile(args)
    captured = capsys.readouterr()
    assert "Keys" in captured.out
    assert "2" in captured.out


def test_run_profile_json_output_is_valid(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET_KEY=abc\nHOST=localhost\n")
    args = make_args(file=str(env_file), json=True)
    run_profile(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["key_count"] == 2
    assert "duplicate_keys" in data


def test_run_profile_json_sensitive_count(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_PASSWORD=secret\nHOST=localhost\n")
    args = make_args(file=str(env_file), json=True)
    run_profile(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["sensitive_key_count"] == 1
