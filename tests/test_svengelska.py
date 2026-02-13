"""Tests for the svengelska checker."""

from svlang.checkers.svengelska import SvengelskaChecker


def test_detects_anglicism():
    c = SvengelskaChecker()
    hits = c.check("Vi måste implementera en ny feature")
    words = {h.word.lower() for h in hits}
    assert "implementera" in words
    assert "feature" in words


def test_suggestion_exists():
    c = SvengelskaChecker()
    hits = c.check("Ge mig lite feedback")
    assert len(hits) == 1
    assert hits[0].word.lower() == "feedback"
    assert "återkoppling" in hits[0].suggestion


def test_no_false_positives():
    c = SvengelskaChecker()
    hits = c.check("Vi ska uppgradera datorn och uppdatera programmet")
    assert len(hits) == 0  # Both are accepted Swedish


def test_case_insensitive():
    c = SvengelskaChecker()
    hits = c.check("FEEDBACK från teamet")
    words = {h.word.lower() for h in hits}
    assert "feedback" in words
    # "team" is accepted, should not be flagged
    assert "team" not in words


def test_custom_terms():
    c = SvengelskaChecker(extra_terms={"kodknack": "programmering"})
    hits = c.check("Lite kodknack i kväll")
    assert len(hits) == 1
    assert hits[0].suggestion == "programmering"


def test_empty_text():
    c = SvengelskaChecker()
    assert c.check("") == []


def test_term_count():
    c = SvengelskaChecker()
    assert c.term_count > 50
