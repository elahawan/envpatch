"""Tests for envpatch.injector."""
from __future__ import annotations

import os
import sys

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.injector import InjectResult, inject_into_environ, run_with_env


def kv(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}")


def comment(text: str) -> EnvEntry:
    return EnvEntry(key=None, value=None, raw=f"# {text}")


def make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# InjectResult helpers
# ---------------------------------------------------------------------------

def test_inject_result_counts():
    r = InjectResult(injected={"A": "1", "B": "2"}, skipped=["C"])
    assert r.inject_count == 2
    assert r.skip_count == 1


def test_inject_result_was_skipped():
    r = InjectResult(injected={}, skipped=["FOO"])
    assert r.was_skipped("FOO")
    assert not r.was_skipped("BAR")


# ---------------------------------------------------------------------------
# inject_into_environ
# ---------------------------------------------------------------------------

def test_inject_sets_env_var(monkeypatch):
    monkeypatch.delenv("_TEST_INJECT_KEY", raising=False)
    env = make_env(kv("_TEST_INJECT_KEY", "hello"))
    result = inject_into_environ(env)
    assert os.environ["_TEST_INJECT_KEY"] == "hello"
    assert result.inject_count == 1


def test_inject_skips_existing_without_overwrite(monkeypatch):
    monkeypatch.setenv("_TEST_SKIP_KEY", "original")
    env = make_env(kv("_TEST_SKIP_KEY", "new"))
    result = inject_into_environ(env, overwrite=False)
    assert os.environ["_TEST_SKIP_KEY"] == "original"
    assert result.skip_count == 1
    assert result.was_skipped("_TEST_SKIP_KEY")


def test_inject_overwrites_when_flag_set(monkeypatch):
    monkeypatch.setenv("_TEST_OW_KEY", "old")
    env = make_env(kv("_TEST_OW_KEY", "new"))
    inject_into_environ(env, overwrite=True)
    assert os.environ["_TEST_OW_KEY"] == "new"


def test_inject_with_prefix(monkeypatch):
    monkeypatch.delenv("APP__TEST_PREFIXED", raising=False)
    env = make_env(kv("_TEST_PREFIXED", "val"))
    result = inject_into_environ(env, prefix="APP_")
    assert os.environ["APP__TEST_PREFIXED"] == "val"
    assert "APP__TEST_PREFIXED" in result.injected


def test_inject_skips_comment_entries(monkeypatch):
    env = make_env(comment("this is a comment"))
    result = inject_into_environ(env)
    assert result.inject_count == 0


# ---------------------------------------------------------------------------
# run_with_env
# ---------------------------------------------------------------------------

def test_run_with_env_passes_variable():
    env = make_env(kv("_ENVPATCH_RUN_TEST", "42"))
    proc = run_with_env(
        [sys.executable, "-c",
         "import os, sys; sys.exit(0 if os.environ.get('_ENVPATCH_RUN_TEST')=='42' else 1)"],
        env,
    )
    assert proc.returncode == 0


def test_run_with_env_extra_env_applied():
    env = make_env()
    proc = run_with_env(
        [sys.executable, "-c",
         "import os, sys; sys.exit(0 if os.environ.get('_EXTRA')=='yes' else 1)"],
        env,
        extra_env={"_EXTRA": "yes"},
    )
    assert proc.returncode == 0
