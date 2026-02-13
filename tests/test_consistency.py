"""Tests for the consistency checker."""

from svlang.checkers.consistency import ConsistencyChecker


def test_detects_inconsistency():
    c = ConsistencyChecker()
    c.add("Save", "Spara", "a.po:1")
    c.add("Save", "Lagra", "b.po:5")
    issues = c.check()
    assert len(issues) == 1
    assert "spara" in issues[0].translations or "Spara" in issues[0].translations


def test_consistent_ok():
    c = ConsistencyChecker()
    c.add("Save", "Spara", "a.po:1")
    c.add("Save", "Spara", "b.po:5")
    assert c.check() == []


def test_case_insensitive():
    c = ConsistencyChecker(case_sensitive=False)
    c.add("Save", "Spara", "a.po:1")
    c.add("Save", "spara", "b.po:5")
    assert c.check() == []


def test_case_sensitive():
    c = ConsistencyChecker(case_sensitive=True)
    c.add("Save", "Spara", "a.po:1")
    c.add("Save", "spara", "b.po:5")
    assert len(c.check()) == 1


def test_multiple_sources():
    c = ConsistencyChecker()
    c.add("Open", "Öppna", "a.po:1")
    c.add("Save", "Spara", "a.po:2")
    c.add("Save", "Lagra", "b.po:3")
    issues = c.check()
    assert len(issues) == 1
    assert issues[0].source == "Save"
