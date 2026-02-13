"""LIX readability index calculator for Swedish text."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class LixResult:
    score: float
    level: str
    words: int
    sentences: int
    long_words: int


# Swedish abbreviations that contain periods but don't end sentences
_ABBREVS = re.compile(
    r'\b(?:t\.ex|bl\.a|dvs|obs|osv|m\.fl|m\.m|s\.k|d\.v\.s|o\.s\.v|f\.d|t\.o\.m|s\.a\.s|ev|kl|nr|st|ca)\.',
    re.IGNORECASE,
)

_SENTENCE_ENDINGS = re.compile(r'[.!?…]+')


class LixCalculator:
    """Calculate the LIX readability index for Swedish text."""

    def calculate(self, text: str) -> LixResult:
        if not text or not text.strip():
            return LixResult(score=0.0, level="Mycket lättläst", words=0, sentences=0, long_words=0)

        # Replace abbreviations with placeholder (no period) to avoid false sentence breaks
        cleaned = _ABBREVS.sub(lambda m: m.group(0).replace('.', '\x00'), text)

        # Count sentences
        sentences = len([s for s in _SENTENCE_ENDINGS.split(cleaned) if s.strip()])
        if sentences == 0:
            sentences = 1

        # Extract words (sequences of word characters including Swedish chars)
        word_list = re.findall(r'[a-zåäöéA-ZÅÄÖÉ\-]+', text)
        word_count = len(word_list)

        if word_count == 0:
            return LixResult(score=0.0, level="Mycket lättläst", words=0, sentences=sentences, long_words=0)

        long_words = sum(1 for w in word_list if len(w) > 6)

        score = (word_count / sentences) + (long_words * 100 / word_count)

        return LixResult(
            score=round(score, 1),
            level=self._classify(score),
            words=word_count,
            sentences=sentences,
            long_words=long_words,
        )

    @staticmethod
    def _classify(score: float) -> str:
        if score < 25:
            return "Mycket lättläst"
        elif score < 35:
            return "Lättläst"
        elif score < 45:
            return "Medelsvår"
        elif score < 55:
            return "Svår"
        else:
            return "Mycket svår"
