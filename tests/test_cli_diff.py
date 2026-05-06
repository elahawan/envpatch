"""Tests for envpatch.cli_diff module."""

import sys
from unittest.mock import patch, mock_open, MagicMock

import pytest

from envpatch.cli_diff import build_parser, run_diff


def make_args(base="base.env", other="other.env", no_color=True, exit_code=False):
    args = MagicMock()
    args.base = base
    args.other = other
    args.no_color = no_color
    args.exit_code = exit_code
    return args


BASE_CONTENT = "KEY=value\nFOO=bar\n"
OTHER_CONTENT = "KEY=value\nFOO=baz\n"
IDENTICAL_CONTENT = "KEY=value\n"


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None
    args = parser.parse_args(["a.env", "b.env"])
    assert args.base == "a.env"
    assert args.other == "b.env"


def test_build_parser_no_color_flag():
    parser = build_parser()
    args = parser.parse_args(["a.env", "b.env", "--no-color"])
    assert args.no_color is True


def test_build_parser_exit_code_flag():
    parser = build_parser()
    args = parser.parse_args(["a.env", "b.env", "--exit-code"])
    args.exit_code is True


def test_run_diff_missing_base(tmp_path, capsys):
    args = make_args(base=str(tmp_path / "missing.env"), other=str(tmp_path / "other.env"))
    code = run_diff(args)
    assert code == 2
    captured = capsys.readouterr()
    assert "base file not found" in captured.err


def test_run_diff_missing_other(tmp_path, capsys):
    base = tmp_path / "base.env"
    base.write_text(BASE_CONTENT)
    args = make_args(base=str(base), other=str(tmp_path / "missing.env"))
    code = run_diff(args)
    assert code == 2
    captured = capsys.readouterr()
    assert "other file not found" in captured.err


def test_run_diff_identical_returns_zero(tmp_path, capsys):
    base = tmp_path / "base.env"
    other = tmp_path / "other.env"
    base.write_text(IDENTICAL_CONTENT)
    other.write_text(IDENTICAL_CONTENT)
    args = make_args(base=str(base), other=str(other), exit_code=True)
    code = run_diff(args)
    assert code == 0


def test_run_diff_different_exit_code_one(tmp_path):
    base = tmp_path / "base.env"
    other = tmp_path / "other.env"
    base.write_text(BASE_CONTENT)
    other.write_text(OTHER_CONTENT)
    args = make_args(base=str(base), other=str(other), exit_code=True)
    code = run_diff(args)
    assert code == 1


def test_run_diff_different_no_exit_code_flag(tmp_path):
    base = tmp_path / "base.env"
    other = tmp_path / "other.env"
    base.write_text(BASE_CONTENT)
    other.write_text(OTHER_CONTENT)
    args = make_args(base=str(base), other=str(other), exit_code=False)
    code = run_diff(args)
    assert code == 0
