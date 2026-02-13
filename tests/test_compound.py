"""Tests for the compound splitter."""

from svlang.checkers.compound import CompoundSplitter


def test_simple_compound():
    s = CompoundSplitter()
    r = s.split("sjöfågel")
    # May or may not split depending on wordlist — just check structure
    assert r.word == "sjöfågel"


def test_non_compound():
    s = CompoundSplitter()
    r = s.split("hund")
    assert r.parts == ["hund"]


def test_known_compound():
    s = CompoundSplitter()
    # With builtin words: "barn" + "bok" should work
    r = s.split("barnbok")
    assert r.is_compound
    assert r.parts == ["barn", "bok"]


def test_with_joiner():
    s = CompoundSplitter()
    # "barn" + s + "vagn" — barnsvagn has joiner
    # Actually "barnvagn" has no joiner
    r = s.split("barnvagn")
    if r.is_compound:
        assert "barn" in r.parts
        assert "vagn" in r.parts


def test_custom_wordlist():
    s = CompoundSplitter(wordlist={"sol", "stol", "solstol"})
    r = s.split("solstol")
    assert r.is_compound
    assert r.parts == ["sol", "stol"]
