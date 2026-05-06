"""Tests for envpatch.parser module."""

from pathlib import Path

import pytest

from envpatch.parser import EnvEntry, EnvFile, parse_env_file, parse_env_text

SAMPLE_ENV = """
# Database config
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb  # production database

SECRET_KEY="super_secret_value"
DEBUG=false
EMPTY_VAR=
"""


def test_parse_basic_entries():
    env = parse_env_text(SAMPLE_ENV)
    keys = [e.key for e in env.entries]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "SECRET_KEY" in keys
    assert "DEBUG" in keys
    assert "EMPTY_VAR" in keys


def test_parse_values():
    env = parse_env_text(SAMPLE_ENV)
    d = env.as_dict
    assert d["DB_HOST"] == "localhost"
    assert d["DB_PORT"] == "5432"
    assert d["DB_NAME"] == "mydb"


def test_inline_comment_stripped():
    env = parse_env_text(SAMPLE_ENV)
    assert env.as_dict["DB_NAME"] == "mydb"


def test_quoted_value_unquoted():
    env = parse_env_text(SAMPLE_ENV)
    assert env.as_dict["SECRET_KEY"] == "super_secret_value"


def test_empty_value():
    env = parse_env_text(SAMPLE_ENV)
    assert env.as_dict["EMPTY_VAR"] == ""


def test_comments_captured():
    env = parse_env_text(SAMPLE_ENV)
    comment_lines = list(env.comments.values())
    assert any("Database config" in c for c in comment_lines)


def test_as_dict():
    env = parse_env_text("FOO=bar\nBAZ=qux")
    assert env.as_dict == {"FOO": "bar", "BAZ": "qux"}


def test_get_existing_key():
    env = parse_env_text("FOO=bar")
    entry = env.get("FOO")
    assert isinstance(entry, EnvEntry)
    assert entry.value == "bar"


def test_get_missing_key():
    env = parse_env_text("FOO=bar")
    assert env.get("MISSING") is None


def test_entry_equality():
    e1 = EnvEntry(key="K", value="v", line_number=1, raw="K=v")
    e2 = EnvEntry(key="K", value="v", line_number=5, raw="K=v")
    e3 = EnvEntry(key="K", value="other", line_number=1, raw="K=other")
    assert e1 == e2
    assert e1 != e3


def test_parse_env_file(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("HOST=127.0.0.1\nPORT=8080\n", encoding="utf-8")
    env = parse_env_file(env_file)
    assert env.path == env_file
    assert env.as_dict == {"HOST": "127.0.0.1", "PORT": "8080"}


def test_parse_env_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        parse_env_file(tmp_path / "nonexistent.env")
