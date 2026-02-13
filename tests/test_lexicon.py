"""Tests for the Swedish lexicon."""

from svlang.checkers.lexicon import SwedishLexicon


def test_lookup_found():
    lex = SwedishLexicon()
    r = lex.lookup("hund")
    assert r.found
    assert "dog" in r.translations


def test_lookup_not_found():
    lex = SwedishLexicon()
    r = lex.lookup("xyznonword")
    assert not r.found
    assert r.translations == []


def test_search():
    lex = SwedishLexicon()
    results = lex.search("bil", limit=5)
    assert len(results) > 0
    assert all(r.word.startswith("bil") for r in results)


def test_reverse_lookup():
    lex = SwedishLexicon()
    results = lex.reverse_lookup("dog", limit=50)
    assert any(r.word == "hund" for r in results)


def test_size():
    lex = SwedishLexicon()
    assert lex.size > 30000


def test_case_insensitive():
    lex = SwedishLexicon()
    r = lex.lookup("Hund")
    assert r.found
