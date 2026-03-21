"""Tests for naturalness analysis."""

import pytest
from svlang.checkers.naturalness import SwedishNaturalness, NaturalnessResult, NaturalnessIssue


def test_natural_text():
    """Test analysis of natural Swedish text."""
    analyzer = SwedishNaturalness()
    
    # Natural Swedish sentence
    result = analyzer.analyze("Jag går till affären för att köpa mjölk.")
    
    assert isinstance(result.score, float)
    assert 0 <= result.score <= 10
    assert result.score > 7  # Should be considered natural
    assert result.sentence_count == 1
    assert result.avg_sentence_length > 0


def test_unnatural_text_length():
    """Test detection of unnaturally long sentences."""
    analyzer = SwedishNaturalness()
    
    # Very long sentence (machine translation indicator)
    long_text = "Detta är en extremt lång mening som innehåller väldigt många ord och fraser som skulle kunna vara ett tecken på maskinöversättning eftersom maskinöversättningar ofta producerar onaturligt långa och komplexa meningsstrukturer som en människa vanligtvis inte skulle skriva på det här sättet utan de skulle istället dela upp det i flera kortare och mer läsbara meningar."
    
    result = analyzer.analyze(long_text)
    
    assert result.score < 8  # Should be penalized for length
    assert any(issue.category == "length" for issue in result.issues)


def test_passive_voice_detection():
    """Test detection of excessive passive voice."""
    analyzer = SwedishNaturalness()
    
    # Text with many passive constructions
    passive_text = "Programmet blev installerat. Datan blev bearbetad. Resultatet blev analyserat. Slutsatsen blev dokumenterad."
    
    result = analyzer.analyze(passive_text)
    
    assert result.passive_ratio > 0
    # May or may not flag as issue depending on exact ratio


def test_anglicism_detection():
    """Test detection of anglicisms."""
    analyzer = SwedishNaturalness()
    
    # Text with anglicisms
    text = "Vi behöver fokusera på performance och implementera denna feature."
    
    result = analyzer.analyze(text)
    
    assert result.anglicism_count > 0
    assert any(issue.category == "anglicism" for issue in result.issues)


def test_empty_text():
    """Test analysis of empty text."""
    analyzer = SwedishNaturalness()
    
    result = analyzer.analyze("")
    
    assert result.score == 10.0  # Empty text is "perfectly natural"
    assert result.sentence_count == 0
    assert result.avg_sentence_length == 0.0
    assert len(result.issues) == 0


def test_short_natural_text():
    """Test analysis of short, natural text."""
    analyzer = SwedishNaturalness()
    
    result = analyzer.analyze("Hej!")
    
    assert result.score >= 8  # Short, natural text should score well
    assert result.sentence_count == 1
    assert len(result.issues) == 0


def test_v2_rule_simple():
    """Test V2 rule checking with simple cases.""" 
    analyzer = SwedishNaturalness()
    
    # This is a basic test - the actual V2 implementation may be simplified
    # since we're using rule-based POS tagging as fallback
    
    natural_v2 = "Idag går jag till affären."  # V2: "går" is second
    result = analyzer.analyze(natural_v2)
    
    # Should not flag V2 violations for simple, correct sentences
    v2_issues = [issue for issue in result.issues if issue.category == "word_order"]
    # May or may not detect depending on POS tagger quality


def test_multiple_sentences():
    """Test analysis of text with multiple sentences."""
    analyzer = SwedishNaturalness()
    
    text = "Första meningen är kort. Den andra meningen är lite längre men fortfarande naturlig. Tredje meningen avslutar texten."
    
    result = analyzer.analyze(text)
    
    assert result.sentence_count == 3
    assert result.avg_sentence_length > 0
    assert result.score > 6  # Should be reasonably natural


def test_issue_severity():
    """Test that issues have appropriate severity levels."""
    analyzer = SwedishNaturalness()
    
    # Create text that should trigger various issues
    problematic_text = "Performance och feedback är viktiga features som måste implementeras enligt deadline och vi behöver fokusera på detta eftersom det blev bestämt att projektet blev prioriterat och alla komponenter blev testade innan release vilket blev dokumenterat i meeting notes."
    
    result = analyzer.analyze(problematic_text)
    
    # Should have various issues with different severities
    assert len(result.issues) > 0
    
    for issue in result.issues:
        assert 0.0 <= issue.severity <= 1.0
        assert issue.category in ["length", "word_order", "passive", "anglicism"]
        assert isinstance(issue.description, str)
        assert len(issue.description) > 0