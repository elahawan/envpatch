"""Tests for envpatch.cli_filter module."""

import argparse
from io import StringIO
from pathlib import Path

import pytest

from envpatch.cli_filter import build_parser, run_filter


def make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        file=".env",
        prefixes=[],
        patterns=[],
        exclude_prefixes=[],
        exclude_patterns=[],
        only_empty=False,
        only_nonempty=False,
        show_excluded=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_parser_has_file_argument():
    parser = build_parser()
    args = parser.parse_args([".env"])
    assert args.file == ".env"


def test_build_parser_prefix_flag():
    parser = build_parser()
    args = parser.parse_args([".env", "--prefix", "DB_"])
    assert "DB_" in args.prefixes


def test_build_parser_only_empty_default_false():
    parser = build_parser()
    args = parser.parse_args([".env"])
    assert args.only_empty is False


def test_build_parser_only_nonempty_flag():
    parser = build_parser()
    args = parser.parse_args([".env", "--only-nonempty"])
    assert args.only_nonempty is True


def test_build_parser_show_excluded_flag():
    parser = build_parser()
    args = parser.parse_args([".env", "--show-excluded"])
    assert args.show_excluded is True


def test_run_filter_missing_file_returns_1():
    args = make_args(file="/nonexistent/.env")
    err = StringIO()
    code = run_filter(args, out=StringIO(), err=err)
    assert code == 1
    assert "not found" in err.getvalue()


def test_run_filter_no_options_returns_all(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nAPI_KEY=secret\n")
    out = StringIO()
    args = make_args(file=str(env_file))
    code = run_filter(args, out=out, err=StringIO())
    assert code == 0
    assert "DB_HOST" in out.getvalue()
    assert "API_KEY" in out.getvalue()


def test_run_filter_prefix_limits_output(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=secret\n")
    out = StringIO()
    args = make_args(file=str(env_file), prefixes=["DB_"])
    code = run_filter(args, out=out, err=StringIO())
    assert code == 0
    output = out.getvalue()
    assert "DB_HOST" in output
    assert "DB_PORT" in output
    assert "API_KEY" not in output


def test_run_filter_show_excluded_inverts_output(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nAPI_KEY=secret\n")
    out = StringIO()
    args = make_args(file=str(env_file), prefixes=["DB_"], show_excluded=True)
    code = run_filter(args, out=out, err=StringIO())
    assert code == 0
    output = out.getvalue()
    assert "API_KEY" in output
    assert "DB_HOST" not in output
