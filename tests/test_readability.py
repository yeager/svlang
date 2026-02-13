"""Tests for LIX readability calculator."""

from svlang.checkers.readability import LixCalculator


calc = LixCalculator()


def test_empty_text():
    r = calc.calculate("")
    assert r.words == 0
    assert r.score == 0.0


def test_simple_sentences():
    text = "Jag gick hem. Det var bra."
    r = calc.calculate(text)
    assert r.sentences == 2
    assert r.words == 6
    assert r.long_words == 0  # no word > 6 chars


def test_long_words_counted():
    text = "Regeringen presenterade proposition."
    r = calc.calculate(text)
    # "Regeringen" (10), "presenterade" (12), "proposition" (11) — all > 6
    assert r.long_words == 3


def test_abbreviations_not_split():
    text = "Vi använder t.ex. Python och bl.a. JavaScript i projektet."
    r = calc.calculate(text)
    assert r.sentences == 1


def test_lix_scale_easy():
    # Short words, multiple sentences → low LIX
    text = "Jag är glad. Du är fin. Vi leker nu."
    r = calc.calculate(text)
    assert r.score < 25
    assert r.level == "Mycket lättläst"


def test_lix_scale_difficult():
    # Long academic-style words, one sentence → high LIX
    text = (
        "Demokratiseringsprocessen i utvecklingsländerna karakteriseras av "
        "institutionella reformer och samhällsförändringar."
    )
    r = calc.calculate(text)
    assert r.score > 55
    assert r.level == "Mycket svår"


def test_classification_boundaries():
    assert calc._classify(24.9) == "Mycket lättläst"
    assert calc._classify(25) == "Lättläst"
    assert calc._classify(34.9) == "Lättläst"
    assert calc._classify(35) == "Medelsvår"
    assert calc._classify(45) == "Svår"
    assert calc._classify(55) == "Mycket svår"
