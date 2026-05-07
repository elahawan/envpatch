"""Tests for envpatch.sorter."""

from envpatch.parser import EnvEntry, EnvFile
from envpatch.sorter import SortOptions, SortOrder, sort_env_file


def kv(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}")


def comment(text: str = "# comment") -> EnvEntry:
    return EnvEntry(key=None, value=None, raw=text)


def blank() -> EnvEntry:
    return EnvEntry(key=None, value=None, raw="")


def make_env(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), path=None)


# ---------------------------------------------------------------------------
# ALPHA order
# ---------------------------------------------------------------------------

def test_sort_alpha_orders_keys():
    env = make_env(kv("ZEBRA"), kv("APPLE"), kv("MANGO"))
    result = sort_env_file(env)
    keys = [e.key for e in result.entries if e.key]
    assert keys == ["APPLE", "MANGO", "ZEBRA"]


def test_sort_alpha_desc_orders_keys_reversed():
    env = make_env(kv("APPLE"), kv("MANGO"), kv("ZEBRA"))
    opts = SortOptions(order=SortOrder.ALPHA_DESC)
    result = sort_env_file(env, opts)
    keys = [e.key for e in result.entries if e.key]
    assert keys == ["ZEBRA", "MANGO", "APPLE"]


def test_sort_original_preserves_order():
    env = make_env(kv("ZEBRA"), kv("APPLE"), kv("MANGO"))
    opts = SortOptions(order=SortOrder.ORIGINAL)
    result = sort_env_file(env, opts)
    keys = [e.key for e in result.entries if e.key]
    assert keys == ["ZEBRA", "APPLE", "MANGO"]


# ---------------------------------------------------------------------------
# Case handling
# ---------------------------------------------------------------------------

def test_sort_case_insensitive_by_default():
    env = make_env(kv("zebra"), kv("APPLE"), kv("Mango"))
    result = sort_env_file(env)
    keys = [e.key for e in result.entries if e.key]
    assert keys == ["APPLE", "Mango", "zebra"]


def test_sort_case_sensitive_when_disabled():
    env = make_env(kv("b_lower"), kv("A_UPPER"))
    opts = SortOptions(ignore_case=False)
    result = sort_env_file(env, opts)
    keys = [e.key for e in result.entries if e.key]
    # uppercase letters sort before lowercase in ASCII
    assert keys == ["A_UPPER", "b_lower"]


# ---------------------------------------------------------------------------
# Comment grouping
# ---------------------------------------------------------------------------

def test_comment_travels_with_following_key():
    c = comment("# section")
    z = kv("ZEBRA")
    a = kv("APPLE")
    env = make_env(c, z, a)
    result = sort_env_file(env)
    entries = result.entries
    # APPLE should come first; comment was attached to ZEBRA so it moves with it
    assert entries[0].key == "APPLE"
    assert entries[1].raw == "# section"
    assert entries[2].key == "ZEBRA"


def test_group_comments_false_puts_comments_first():
    c = comment("# note")
    b = kv("BETA")
    a = kv("ALPHA")
    env = make_env(c, b, a)
    opts = SortOptions(group_comments=False)
    result = sort_env_file(env, opts)
    assert result.entries[0].raw == "# note"
    assert result.entries[1].key == "ALPHA"
    assert result.entries[2].key == "BETA"


def test_trailing_comments_preserved_at_end():
    env = make_env(kv("ZEBRA"), kv("APPLE"), blank(), comment("# end"))
    result = sort_env_file(env)
    last_two = result.entries[-2:]
    assert last_two[0].raw == ""
    assert last_two[1].raw == "# end"


# ---------------------------------------------------------------------------
# Return type and immutability
# ---------------------------------------------------------------------------

def test_returns_new_env_file_instance():
    env = make_env(kv("A"), kv("B"))
    result = sort_env_file(env)
    assert result is not env


def test_original_env_file_unchanged():
    env = make_env(kv("ZEBRA"), kv("APPLE"))
    _ = sort_env_file(env)
    assert env.entries[0].key == "ZEBRA"
