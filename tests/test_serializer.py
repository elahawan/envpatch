"""Tests for envpatch.serializer module."""

import os
import tempfile
import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.serializer import serialize, write_env_file, _needs_quoting, _quote


def make_env(*pairs) -> EnvFile:
    entries = [EnvEntry(key=k, value=v) for k, v in pairs]
    return EnvFile(entries=entries)


def test_serialize_simple_entries():
    env = make_env(("A", "1"), ("B", "2"))
    output = serialize(env)
    assert "A=1" in output
    assert "B=2" in output


def test_serialize_empty_value():
    env = make_env(("EMPTY", ""))
    output = serialize(env)
    assert "EMPTY=" in output


def test_serialize_none_value():
    env = make_env(("KEY", None))
    output = serialize(env)
    assert "KEY=" in output


def test_serialize_with_quoting_forced():
    env = make_env(("MSG", "hello world"))
    output = serialize(env, quote_values=True)
    assert 'MSG="hello world"' in output


def test_serialize_auto_quotes_spaces():
    env = make_env(("MSG", "hello world"))
    output = serialize(env)
    assert '"hello world"' in output


def test_serialize_comment_only_entry():
    entries = [
        EnvEntry(key=None, value=None, comment="# Section header"),
        EnvEntry(key="A", value="1"),
    ]
    env = EnvFile(entries=entries)
    output = serialize(env)
    assert "# Section header" in output
    assert "A=1" in output


def test_serialize_blank_line():
    entries = [
        EnvEntry(key="A", value="1"),
        EnvEntry(key=None, value=None, comment=None),
        EnvEntry(key="B", value="2"),
    ]
    env = EnvFile(entries=entries)
    output = serialize(env)
    lines = output.split("\n")
    assert "" in lines


def test_needs_quoting_with_space():
    assert _needs_quoting("hello world") is True


def test_needs_quoting_plain():
    assert _needs_quoting("plain") is False


def test_quote_wraps_value():
    assert _quote("hello") == '"hello"'


def test_quote_escapes_inner_quotes():
    assert _quote('say "hi"') == '"say \\"hi\\""'


def test_write_env_file_creates_file():
    env = make_env(("FOO", "bar"), ("BAZ", "qux"))
    with tempfile.NamedTemporaryFile(mode="r", suffix=".env", delete=False) as f:
        path = f.name
    try:
        write_env_file(env, path)
        with open(path) as f:
            content = f.read()
        assert "FOO=bar" in content
        assert "BAZ=qux" in content
        assert content.endswith("\n")
    finally:
        os.unlink(path)
