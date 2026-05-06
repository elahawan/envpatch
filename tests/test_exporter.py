"""Tests for envpatch.exporter."""

import json
import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.exporter import (
    ExportFormat,
    export_as_json,
    export_as_yaml,
    export_as_shell,
    export_env,
)


def make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(entries=entries)


def test_export_json_basic():
    env = make_env(("FOO", "bar"), ("BAZ", "qux"))
    result = json.loads(export_as_json(env))
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_export_json_empty_value():
    env = make_env(("EMPTY", ""))
    result = json.loads(export_as_json(env))
    assert result["EMPTY"] == ""


def test_export_json_skips_comment_entries():
    entries = [
        EnvEntry(key=None, value=None, raw="# a comment"),
        EnvEntry(key="KEY", value="val", raw="KEY=val"),
    ]
    env = EnvFile(entries=entries)
    result = json.loads(export_as_json(env))
    assert list(result.keys()) == ["KEY"]


def test_export_yaml_basic():
    env = make_env(("HOST", "localhost"), ("PORT", "5432"))
    output = export_as_yaml(env)
    assert "HOST: localhost" in output
    assert "PORT: 5432" in output


def test_export_yaml_quotes_special_chars():
    env = make_env(("DSN", "postgres://host:5432/db"))
    output = export_as_yaml(env)
    assert '"postgres://host:5432/db"' in output


def test_export_shell_has_shebang():
    env = make_env(("FOO", "bar"))
    output = export_as_shell(env)
    assert output.startswith("#!/usr/bin/env sh")


def test_export_shell_export_statement():
    env = make_env(("MY_VAR", "hello world"))
    output = export_as_shell(env)
    assert "export MY_VAR='hello world'" in output


def test_export_shell_escapes_single_quotes():
    env = make_env(("TRICKY", "it's alive"))
    output = export_as_shell(env)
    assert "export TRICKY='it'\"'\"'s alive'" in output


def test_export_env_dispatch_json():
    env = make_env(("A", "1"))
    result = export_env(env, ExportFormat.JSON)
    assert json.loads(result) == {"A": "1"}


def test_export_env_dispatch_yaml():
    env = make_env(("A", "1"))
    result = export_env(env, ExportFormat.YAML)
    assert "A: 1" in result


def test_export_env_dispatch_shell():
    env = make_env(("A", "1"))
    result = export_env(env, ExportFormat.SHELL)
    assert "export A='1'" in result


def test_export_env_invalid_format():
    env = make_env(("A", "1"))
    with pytest.raises(ValueError, match="Unsupported"):
        export_env(env, "toml")  # type: ignore[arg-type]
