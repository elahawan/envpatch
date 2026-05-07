"""Tests for envpatch.comparator."""

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.comparator import compare_coverage, CoverageReport


def make_env(*keys) -> EnvFile:
    """Build an EnvFile whose entries are simple KEY=value pairs."""
    entries = [EnvEntry(key=k, value="val", comment=None, raw=f"{k}=val") for k in keys]
    return EnvFile(entries=entries)


# ---------------------------------------------------------------------------
# compare_coverage
# ---------------------------------------------------------------------------

def test_identical_keys_are_common():
    ref = make_env("A", "B", "C")
    tgt = make_env("A", "B", "C")
    report = compare_coverage(ref, tgt)
    assert report.common_keys == {"A", "B", "C"}
    assert report.only_in_reference == set()
    assert report.only_in_target == set()


def test_missing_keys_detected():
    ref = make_env("A", "B", "C")
    tgt = make_env("A")
    report = compare_coverage(ref, tgt)
    assert report.only_in_reference == {"B", "C"}
    assert report.common_keys == {"A"}


def test_extra_keys_detected():
    ref = make_env("A")
    tgt = make_env("A", "EXTRA")
    report = compare_coverage(ref, tgt)
    assert report.only_in_target == {"EXTRA"}
    assert report.only_in_reference == set()


def test_completely_disjoint_files():
    ref = make_env("X", "Y")
    tgt = make_env("Z")
    report = compare_coverage(ref, tgt)
    assert report.common_keys == set()
    assert report.only_in_reference == {"X", "Y"}
    assert report.only_in_target == {"Z"}


def test_empty_files():
    ref = make_env()
    tgt = make_env()
    report = compare_coverage(ref, tgt)
    assert report.common_keys == set()
    assert report.only_in_reference == set()
    assert report.only_in_target == set()


# ---------------------------------------------------------------------------
# CoverageReport helpers
# ---------------------------------------------------------------------------

def test_coverage_ratio_full():
    ref = make_env("A", "B")
    tgt = make_env("A", "B")
    report = compare_coverage(ref, tgt)
    assert report.coverage_ratio == 1.0


def test_coverage_ratio_partial():
    ref = make_env("A", "B", "C", "D")
    tgt = make_env("A", "B")
    report = compare_coverage(ref, tgt)
    assert report.coverage_ratio == pytest.approx(0.5)


def test_coverage_ratio_empty_reference():
    ref = make_env()
    tgt = make_env("A")
    report = compare_coverage(ref, tgt)
    assert report.coverage_ratio == 1.0


def test_is_complete_true():
    ref = make_env("A", "B")
    tgt = make_env("A", "B", "C")
    report = compare_coverage(ref, tgt)
    assert report.is_complete() is True


def test_is_complete_false():
    ref = make_env("A", "B")
    tgt = make_env("A")
    report = compare_coverage(ref, tgt)
    assert report.is_complete() is False


def test_missing_keys_sorted():
    ref = make_env("C", "A", "B")
    tgt = make_env()
    report = compare_coverage(ref, tgt)
    assert report.missing_keys == ["A", "B", "C"]


def test_extra_keys_sorted():
    ref = make_env()
    tgt = make_env("Z", "M", "A")
    report = compare_coverage(ref, tgt)
    assert report.extra_keys == ["A", "M", "Z"]


def test_paths_stored_on_report():
    ref = make_env("A")
    tgt = make_env("A")
    report = compare_coverage(ref, tgt,
                              reference_path=".env.example",
                              target_path=".env.production")
    assert report.reference_path == ".env.example"
    assert report.target_path == ".env.production"
