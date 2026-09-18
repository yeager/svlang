"""Swedish word frequency analysis."""

from __future__ import annotations

import re
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import NamedTuple


DATA_DIR = Path(__file__).parent.parent / "data"


def _normalize(word: str) -> str:
    return unicodedata.normalize("NFC", word.strip().lower())


class FrequencyResult(NamedTuple):
    """Result from frequency analysis."""
    word: str
    frequency_score: float  # 0.0 = most common, 1.0 = very rare/unknown
    found: bool  # Present in the frequency list; not a spelling verdict.
    rank: int | None  # Position in frequency list (1-based), None if not found


class SwedishFrequency:
    """Swedish word frequency analyzer using top 10k word list."""
    
    def __init__(self):
        self._load_frequency_data()
        self._load_lexicon()

    def _load_lexicon(self):
        """Load the bundled lexicon to distinguish valid words from unknown ones."""
        lexicon_path = DATA_DIR / "sv_wordlist.txt"
        self.lexicon = set()
        if lexicon_path.exists():
            with lexicon_path.open(encoding="utf-8") as f:
                self.lexicon = {
                    _normalize(line)
                    for line in f
                    if line.strip() and not line.startswith("#")
                }
        # lookup uses Folkets lexikon, which contains words absent from the
        # Hunspell-derived wordlist. Both bundled resources establish coverage.
        dictionary_path = DATA_DIR / "folkets_sv_en.tsv"
        if dictionary_path.exists():
            with dictionary_path.open(encoding="utf-8") as f:
                self.lexicon.update(
                    _normalize(line.split("\t", 1)[0])
                    for line in f
                    if "\t" in line and not line.startswith("#")
                )
    
    def _load_frequency_data(self):
        """Load frequency data from built-in word list."""
        # Package data is read-only. A missing resource is an installation
        # error, not a reason to generate estimated data inside site-packages.
        self.word_to_rank = {}
        with (DATA_DIR / "sv_frequency_10k.txt").open(encoding="utf-8") as f:
            for line in f:
                word = _normalize(line)
                if word and not word.startswith("#") and word not in self.word_to_rank:
                    self.word_to_rank[word] = len(self.word_to_rank) + 1
        self.total_words = len(self.word_to_rank)

    def get_frequency_score(self, word: str) -> FrequencyResult:
        """Get frequency score for a word.
        
        Args:
            word: Word to analyze
            
        Returns:
            FrequencyResult with score (0.0=common, 1.0=rare) and rank info
        """
        word_clean = re.sub(r'[^\w\-]', '', _normalize(word))
        
        if word_clean in self.word_to_rank:
            rank = self.word_to_rank[word_clean]
            # Convert rank to score: rank 1 = score 0.0, rank 10000 = score 1.0
            score = (rank - 1) / max(1, self.total_words - 1)
            return FrequencyResult(word, score, True, rank)
        else:
            # Word not found = very rare/unknown
            return FrequencyResult(word, 1.0, False, None)
    
    def _hunspell_known_words(self, words: set[str]) -> set[str]:
        """Return words accepted by an installed Swedish Hunspell dictionary.

        The compact frequency list measures commonness, while Hunspell provides
        morphological coverage for valid inflections such as ``enheten``.
        The optional lookup keeps this package usable where Hunspell is absent.
        """
        # Hunspell can split identifiers at digits/underscores and report only
        # the fragments, which cannot be matched to our original tokens.
        words = {word for word in words if word.isalpha()}
        if not words or not shutil.which("hunspell"):
            return set()
        try:
            result = subprocess.run(
                ["hunspell", "-d", "sv_SE", "-l"],
                input="\n".join(words) + "\n", text=True, capture_output=True,
                check=False, timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return set()
        # Empty output only means all words were accepted after a successful
        # lookup. Missing dictionaries and other failures must not hide typos.
        if result.returncode != 0 or result.stderr.strip():
            return set()
        misspelled = {_normalize(line) for line in result.stdout.splitlines() if line.strip()}
        return words - misspelled

    def analyze_text(self, text: str, threshold: float = 0.7) -> list[FrequencyResult]:
        """Analyze text for rare or unknown words.

        Valid lexicon words and Hunspell-recognized inflections are excluded:
        the bundled top-10k list measures frequency, not spelling correctness.
        """
        words = set(re.findall(r'\b\w+\b', _normalize(text)))
        candidates = [
            self.get_frequency_score(word)
            for word in words
            if len(word) >= 3 and not word.isdecimal() and word not in self.lexicon
        ]
        candidates = [r for r in candidates if r.frequency_score >= threshold]
        known_words = self._hunspell_known_words({r.word for r in candidates})
        return sorted(
            (r for r in candidates if r.word not in known_words),
            key=lambda r: (-r.frequency_score, r.word),
        )

    def get_word_rarity_level(self, score: float) -> str:
        """Get human-readable rarity level."""
        if score < 0.1:
            return "mycket vanligt"
        elif score < 0.3:
            return "vanligt"
        elif score < 0.5:
            return "ganska vanligt"
        elif score < 0.7:
            return "ovanligt"
        elif score < 0.9:
            return "sällsynt"
        else:
            return "mycket sällsynt/ej frekvensbedömt"
