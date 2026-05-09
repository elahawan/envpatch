"""Tests for envpatch.cli_diff_summary."""

import argparse
import json
from unittest.mock import patch, mock_open, MagicMock

import pytest

from envpatch.cli_diff_summary import build_parser, run_summary


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "base": "base.env",
        "other": "other.env",
        "as_json": False,
        "no_color": False,
        "exit_code": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


BASE_CONTENT = "A=1\nB=2\n"
OTHER_CONTENT = "A=1\nB=99\nC=3\n"


def test_build_parser_returns_parser():
    assert isinstance(build_parser(), argparse.ArgumentParser)


def test_build_parser_has_base_and_other():
    parser = build_parser()
    args = parser.parse_args(["base.env", "other.env"])
    assert args.base == "base.env"
    assert args.other == "other.env"


def test_build_parser_json_flag_default_false():
    parser = build_parser()
    args = parser.parse_args(["a.env", "b.env"])
    assert args.as_json is False


def test_build_parser_json_flag_set():
    parser = build_parser()
    args = parser.parse_args(["a.env", "b.env", "--json"])
    assert args.as_json is True


def test_build_parser_no_color_flag():
    parser = build_parser()
    args = parser.parse_args(["a.env", "b.env", "--no-color"])
    assert args.no_color is True


def test_build_parser_exit_code_flag():
    parser = build_parser()
    args = parser.parse_args(["a.env", "b.env", "--exit-code"])
    assert args.exit_code is True


def _open_side_effect(base_content, other_content):
    """Return a side_effect for builtins.open that serves two files."""
    call_count = [0]
    contents = [base_content, other_content]

    def side_effect(path, *a, **kw):
        idx = call_count[0]
        call_count[0] += 1
        m = mock_open(read_data=contents[idx])()
        return m

    return side_effect


def test_run_summary_missing_base_returns_2(tmp_path, capsys):
    args = make_args(base=str(tmp_path / "missing.env"), other=str(tmp_path / "other.env"))
    code = run_summary(args)
    assert code == 2
    captured = capsys.readouterr()
    assert "base" in captured.err


def test_run_summary_missing_other_returns_2(tmp_path, capsys):
    base = tmp_path / "base.env"
    base.write_text("A=1\n")
    args = make_args(base=str(base), other=str(tmp_path / "missing.env"))
    code = run_summary(args)
    assert code == 2


def test_run_summary_identical_returns_0(tmp_path, capsys):
    f = tmp_path / "env"
    f.write_text("A=1\nB=2\n")
    args = make_args(base=str(f), other=str(f))
    code = run_summary(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "identical" in out.lower()


def test_run_summary_exit_code_on_diff(tmp_path):
    base = tmp_path / "base.env"
    other = tmp_path / "other.env"
    base.write_text("A=1\n")
    other.write_text("A=99\n")
    args = make_args(base=str(base), other=str(other), exit_code=True)
    code = run_summary(args)
    assert code == 1


def test_run_summary_json_output(tmp_path, capsys):
    f = tmp_path / "env"
    f.write_text("A=1\n")
    args = make_args(base=str(f), other=str(f), as_json=True)
    run_summary(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "added" in data
    assert "removed" in data
    assert "changed" in data
