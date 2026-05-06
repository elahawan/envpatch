"""Tests for envpatch.cli_export."""

import json
from pathlib import Path

import pytest

from envpatch.cli_export import build_parser, run_export


def make_args(file: str, fmt: str = "json", output: str | None = None):
    class Args:
        pass

    a = Args()
    a.file = file
    a.format = fmt
    a.output = output
    return a


def test_build_parser_returns_parser():
    p = build_parser()
    assert p is not None


def test_build_parser_default_format():
    p = build_parser()
    args = p.parse_args(["some.env"])
    assert args.format == "json"


def test_build_parser_accepts_yaml():
    p = build_parser()
    args = p.parse_args(["some.env", "--format", "yaml"])
    assert args.format == "yaml"


def test_build_parser_accepts_shell():
    p = build_parser()
    args = p.parse_args(["some.env", "-f", "shell"])
    assert args.format == "shell"


def test_run_export_missing_file(tmp_path):
    args = make_args(str(tmp_path / "nonexistent.env"))
    result = run_export(args)
    assert result == 1


def test_run_export_json_to_stdout(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")
    args = make_args(str(env_file), fmt="json")
    result = run_export(args)
    assert result == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data == {"FOO": "bar", "BAZ": "qux"}


def test_run_export_yaml_to_stdout(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("HOST=localhost\n")
    args = make_args(str(env_file), fmt="yaml")
    result = run_export(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "HOST: localhost" in captured.out


def test_run_export_shell_to_stdout(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("MY_VAR=hello\n")
    args = make_args(str(env_file), fmt="shell")
    result = run_export(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "export MY_VAR='hello'" in captured.out


def test_run_export_writes_to_output_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=value\n")
    out_file = tmp_path / "out.json"
    args = make_args(str(env_file), fmt="json", output=str(out_file))
    result = run_export(args)
    assert result == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert data == {"KEY": "value"}
