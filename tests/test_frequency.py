"""Tests for frequency analysis."""

import pytest
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
    assert freq.get_word_rarity_level(0.95) == "mycket sällsynt/okänt"


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


def test_frequency_text_analysis_skips_hunspell_inflections():
    """Swedish inflections are valid even when the simple lexicon has lemmas."""
    freq = SwedishFrequency()
    assert not any(item.word == "enheten" for item in freq.analyze_text("enheten", threshold=0.7))
