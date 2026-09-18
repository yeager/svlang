"""Tests for frequency analysis."""

import subprocess
import unicodedata

import pytest

from svlang.checkers import frequency
from svlang.checkers.frequency import SwedishFrequency, FrequencyResult


def test_frequency_common_words():
    """Test frequency analysis with common words."""
    freq = SwedishFrequency()
    
    # Common words should have low scores (close to 0.0)
    result = freq.get_frequency_score("och")
    assert result.found
    assert result.frequency_score < 0.1
    assert result.rank is not None
    assert result.rank <= 10  # Should be very high ranking
    
    result = freq.get_frequency_score("att")  
    assert result.found
    assert result.frequency_score < 0.1


def test_frequency_rare_words():
    """Test frequency analysis with rare/unknown words."""
    freq = SwedishFrequency()
    
    # Made-up word should not be found
    result = freq.get_frequency_score("zyx123nonsens")
    assert not result.found
    assert result.frequency_score == 1.0
    assert result.rank is None


def test_frequency_text_analysis():
    """Test text analysis for rare words.""" 
    freq = SwedishFrequency()
    
    # Text with mix of common and rare words
    text = "och att det är helt vanliga ord men zyx123nonsens är okänt"
    rare_words = freq.analyze_text(text, threshold=0.5)
    
    # Should find some rare words - check that function returns results
    assert isinstance(rare_words, list)
    # At least some words should be found as rare/unknown
    assert len(rare_words) > 0


def test_rarity_levels():
    """Test rarity level descriptions."""
    freq = SwedishFrequency()
    
    assert freq.get_word_rarity_level(0.05) == "mycket vanligt"
    assert freq.get_word_rarity_level(0.2) == "vanligt" 
    assert freq.get_word_rarity_level(0.4) == "ganska vanligt"
    assert freq.get_word_rarity_level(0.6) == "ovanligt"
    assert freq.get_word_rarity_level(0.8) == "sällsynt"
    assert freq.get_word_rarity_level(0.95) == "mycket sällsynt/ej frekvensbedömt"


def test_frequency_edge_cases():
    """Test edge cases in frequency analysis."""
    freq = SwedishFrequency()
    
    # Empty string
    result = freq.get_frequency_score("")
    assert not result.found
    
    # Single character
    result = freq.get_frequency_score("a")
    # May or may not be found, but shouldn't crash
    assert isinstance(result.frequency_score, float)
    
    # Word with punctuation
    result = freq.get_frequency_score("hej!")
    # Should clean and analyze "hej" 
    assert result.word == "hej!"

def test_frequency_text_analysis_skips_valid_lexicon_words_outside_top_list():
    """Known Swedish words outside the compact frequency list are not unknown."""
    freq = SwedishFrequency()
    assert "välkommen" in freq.lexicon
    assert not any(item.word == "välkommen" for item in freq.analyze_text("välkommen", threshold=0.7))


def test_frequency_text_analysis_skips_hunspell_inflections(monkeypatch):
    """Swedish inflections are valid even when the simple lexicon has lemmas."""
    monkeypatch.setattr(frequency.shutil, "which", lambda _: "/usr/bin/hunspell")
    monkeypatch.setattr(frequency.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a, 0, "", ""))
    freq = SwedishFrequency()
    assert not any(item.word == "enheten" for item in freq.analyze_text("enheten", threshold=0.7))


@pytest.fixture(autouse=True)
def no_system_hunspell(monkeypatch):
    """Unit tests must also work without system dictionaries installed."""
    monkeypatch.setattr(frequency.shutil, "which", lambda _: None)


def test_both_bundled_lexicons_are_used_without_hunspell():
    freq = SwedishFrequency()
    for word in ("välkommen", "abstinensprocess", "administrationskostnader"):
        assert word not in freq.word_to_rank
        assert not freq.analyze_text(word)
    assert not freq.analyze_text(unicodedata.normalize("NFD", "VÄLKOMMEN"))
    assert [r.word for r in freq.analyze_text("qzxqzxqzx")] == ["qzxqzxqzx"]


@pytest.mark.parametrize("returncode,stderr", [(1, ""), (0, "dictionary missing"), (1, "dictionary missing")])
def test_hunspell_failure_does_not_accept_unknown_words(monkeypatch, returncode, stderr):
    monkeypatch.setattr(frequency.shutil, "which", lambda _: "/usr/bin/hunspell")
    monkeypatch.setattr(frequency.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a, returncode, "", stderr))
    assert [r.word for r in SwedishFrequency().analyze_text("qzxqzxqzx")] == ["qzxqzxqzx"]


@pytest.mark.parametrize("error", [OSError("cannot execute"), subprocess.TimeoutExpired("hunspell", 10)])
def test_hunspell_exception_keeps_unknown_words(monkeypatch, error):
    monkeypatch.setattr(frequency.shutil, "which", lambda _: "/usr/bin/hunspell")
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(frequency.subprocess, "run", fail)
    assert [r.word for r in SwedishFrequency().analyze_text("qzxqzxqzx")] == ["qzxqzxqzx"]


def test_hunspell_only_receives_candidates_and_preserves_misspellings(monkeypatch):
    monkeypatch.setattr(frequency.shutil, "which", lambda _: "/usr/bin/hunspell")
    def run(*args, **kwargs):
        assert set(kwargs["input"].splitlines()) == {"enheten", "qzxqzxqzx"}
        return subprocess.CompletedProcess(args, 0, "qzxqzxqzx\n", "")
    monkeypatch.setattr(frequency.subprocess, "run", run)
    assert [r.word for r in SwedishFrequency().analyze_text("välkommen enheten qzxqzxqzx 1234")] == ["qzxqzxqzx"]


def test_ranks_exclude_comments_blanks_and_duplicates(monkeypatch, tmp_path):
    monkeypatch.setattr(frequency, "DATA_DIR", tmp_path)
    (tmp_path / "sv_frequency_10k.txt").write_text("# comment\noch\n\natt\noch\när\n", encoding="utf-8")
    freq = SwedishFrequency()
    assert freq.total_words == 3
    assert freq.get_frequency_score("och").rank == 1
    assert freq.get_frequency_score("och").frequency_score == 0.0
    assert freq.get_frequency_score("är").frequency_score == 1.0


@pytest.mark.parametrize("content", ["", "och\n"])
def test_empty_and_single_word_frequency_lists(monkeypatch, tmp_path, content):
    monkeypatch.setattr(frequency, "DATA_DIR", tmp_path)
    (tmp_path / "sv_frequency_10k.txt").write_text(content, encoding="utf-8")
    result = SwedishFrequency().get_frequency_score("och")
    assert result.frequency_score == (0.0 if content else 1.0)


def test_missing_frequency_resource_does_not_write_package_data(monkeypatch, tmp_path):
    monkeypatch.setattr(frequency, "DATA_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        SwedishFrequency()
    assert not list(tmp_path.iterdir())


def test_unknown_results_have_stable_order():
    words = [r.word for r in SwedishFrequency().analyze_text("zzqxzz aaqqzz mmqqzz")]
    assert words == sorted(words)


def test_hunspell_does_not_silently_accept_mixed_tokens(monkeypatch):
    monkeypatch.setattr(frequency.shutil, "which", lambda _: "/usr/bin/hunspell")
    def run(*args, **kwargs):
        pytest.fail("mixed tokens must not be sent to Hunspell")
    monkeypatch.setattr(frequency.subprocess, "run", run)
    assert [r.word for r in SwedishFrequency().analyze_text("zyx123nonsens")] == ["zyx123nonsens"]
