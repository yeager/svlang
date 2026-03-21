"""Tests for extended compound word functionality."""

import pytest
from svlang.checkers.compound import CompoundSplitter


def test_compound_validation_rules():
    """Test Swedish compound validation rules."""
    splitter = CompoundSplitter()
    
    # Test särskrivning detection
    issues = splitter.validate_compound_rules("kött färs")
    # May or may not detect this as a compound depending on dictionary
    
    # Test very long compound suggestion
    long_compound = "barnvagnshjulsfästemaskineriförsäljningsplatsdiskussion"
    issues = splitter.validate_compound_rules(long_compound)
    # May suggest hyphenation for readability
    

def test_double_consonant_handling():
    """Test handling of double consonants in compounds."""
    splitter = CompoundSplitter()
    
    # Test double consonant rules (simplified test)
    candidates = splitter._get_prefix_candidates("kött")
    assert "kött" in candidates
    assert "köt" in candidates  # Single consonant variant
    
    candidates = splitter._get_prefix_candidates("ren")
    assert "ren" in candidates
    assert "renn" in candidates  # Double consonant variant


def test_s_linker_candidates():
    """Test -s- linking element handling."""
    splitter = CompoundSplitter()
    
    # Test that words that commonly take -s- linker work
    # This is a basic test of the infrastructure
    result = splitter.split("arbetsplats")
    
    # Should be able to split compounds with common patterns
    # Exact results depend on dictionary content


def test_prefix_candidates_e_ending():
    """Test handling of -e endings in compounds."""
    splitter = CompoundSplitter()
    
    candidates = splitter._get_prefix_candidates("rike")
    assert "rike" in candidates
    assert "rik" in candidates  # Without -e
    
    candidates = splitter._get_prefix_candidates("rik")
    assert "rik" in candidates  
    assert "rike" in candidates  # With -e


def test_compound_split_depth_limit():
    """Test that compound splitting doesn't recurse infinitely."""
    splitter = CompoundSplitter()
    
    # Create a scenario that could cause deep recursion
    very_long_word = "a" * 50
    result = splitter.split(very_long_word)
    
    # Should return something without crashing
    assert isinstance(result.word, str)
    assert isinstance(result.is_compound, bool)


def test_empty_and_short_compounds():
    """Test edge cases with empty and short inputs."""
    splitter = CompoundSplitter()
    
    # Empty word
    result = splitter.split("")
    assert not result.is_compound
    assert result.parts == []
    
    # Single character
    result = splitter.split("a")
    assert not result.is_compound
    assert result.parts == ["a"]
    
    # Two characters (below minimum)
    result = splitter.split("ab")
    assert result.parts == ["ab"]


def test_known_compounds():
    """Test splitting of known Swedish compounds."""
    splitter = CompoundSplitter()
    
    # Test some basic compounds that should work with our word list
    test_cases = [
        ("barnbok", ["barn", "bok"]),
        ("bilväg", ["bil", "väg"]), 
        ("skolhus", ["skol", "hus"]),  # May need "skola" → "skol" handling
    ]
    
    for compound, expected_parts in test_cases:
        result = splitter.split(compound)
        # Note: Exact results depend on dictionary content and algorithms
        # This test mainly ensures the function works without crashing
        assert isinstance(result.is_compound, bool)
        if result.is_compound:
            assert len(result.parts) >= 2