"""Tests for envpatch.cli_patch."""

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envpatch.cli_patch import build_parser, run_patch
from envpatch.merger import ConflictStrategy


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "base": "base.env",
        "patch": "patch.env",
        "output": None,
        "strategy": ConflictStrategy.THEIRS.value,
        "dry_run": False,
        "no_color": True,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_parser_has_base_and_patch():
    parser = build_parser()
    args = parser.parse_args(["base.env", "patch.env"])
    assert args.base == "base.env"
    assert args.patch == "patch.env"


def test_build_parser_dry_run_flag():
    parser = build_parser()
    args = parser.parse_args(["base.env", "patch.env", "--dry-run"])
    assert args.dry_run is True


def test_build_parser_strategy_default():
    parser = build_parser()
    args = parser.parse_args(["base.env", "patch.env"])
    assert args.strategy == ConflictStrategy.THEIRS.value


def test_run_patch_missing_base(tmp_path):
    args = make_args(base=str(tmp_path / "missing.env"), patch=str(tmp_path / "patch.env"))
    result = run_patch(args)
    assert result == 1


def test_run_patch_missing_patch(tmp_path):
    base = tmp_path / "base.env"
    base.write_text("KEY=value\n")
    args = make_args(base=str(base), patch=str(tmp_path / "missing.env"))
    result = run_patch(args)
    assert result == 1


def test_run_patch_dry_run_no_write(tmp_path, capsys):
    base = tmp_path / "base.env"
    patch_file = tmp_path / "patch.env"
    base.write_text("KEY=old\n")
    patch_file.write_text("KEY=new\n")
    args = make_args(base=str(base), patch=str(patch_file), dry_run=True)
    result = run_patch(args)
    assert result == 0
    assert base.read_text() == "KEY=old\n"
    captured = capsys.readouterr()
    assert "dry-run" in captured.out


def test_run_patch_writes_output(tmp_path):
    base = tmp_path / "base.env"
    patch_file = tmp_path / "patch.env"
    out_file = tmp_path / "out.env"
    base.write_text("KEY=old\n")
    patch_file.write_text("KEY=new\n")
    args = make_args(base=str(base), patch=str(patch_file), output=str(out_file))
    result = run_patch(args)
    assert result == 0
    assert out_file.exists()
    assert "KEY" in out_file.read_text()


def test_run_patch_added_key(tmp_path):
    base = tmp_path / "base.env"
    patch_file = tmp_path / "patch.env"
    base.write_text("EXISTING=1\n")
    patch_file.write_text("EXISTING=1\nNEW_KEY=hello\n")
    args = make_args(base=str(base), patch=str(patch_file))
    result = run_patch(args)
    assert result == 0
    content = base.read_text()
    assert "NEW_KEY" in content
