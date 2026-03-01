"""Swedish compound word splitter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class CompoundSplit:
    """Result of splitting a compound word."""
    word: str
    parts: list[str]
    is_compound: bool


class CompoundSplitter:
    """Split Swedish compound words into components.
    
    Uses a dictionary-based approach: tries to find the longest prefix
    that's a known word, then recursively splits the remainder.
    
    Usage:
        splitter = CompoundSplitter()
        result = splitter.split("barnvagnshjul")
        # → CompoundSplit(word="barnvagnshjul", parts=["barn", "vagn", "hjul"], is_compound=True)
    """

    # Common compound join letters (fogmorfem)
    _JOINERS = ("s", "e", "o", "u", "")

    def __init__(self, wordlist: set[str] | None = None):
        if wordlist is not None:
            self._words = wordlist
        else:
            self._words = self._load_default_wordlist()
        self._min_part_len = 2

    @staticmethod
    def _load_default_wordlist() -> set[str]:
        """Load a basic Swedish wordlist."""
        wl_path = Path(__file__).parent.parent / "data" / "sv_wordlist.txt"
        if wl_path.exists():
            return {
                line.strip().lower()
                for line in wl_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")
            }
        # Fallback: minimal built-in set of common Swedish words
        return _BUILTIN_WORDS

    def split(self, word: str) -> CompoundSplit:
        """Try to split a compound word into parts."""
        if not word or len(word) < 2:
            return CompoundSplit(word=word, parts=[word] if word else [], is_compound=False)
        word_lower = word.lower()
        parts = self._try_split(word_lower)
        if parts and len(parts) > 1:
            return CompoundSplit(word=word, parts=parts, is_compound=True)
        return CompoundSplit(word=word, parts=[word], is_compound=False)

    def _try_split(self, word: str, depth: int = 0) -> list[str] | None:
        """Recursive compound splitting."""
        if depth > 5:
            return None
        if len(word) < self._min_part_len * 2:
            if word in self._words:
                return [word]
            return None

        # Try splitting at every position — longest prefix first
        # This prefers "sjukhus+byggnad" over "sjuk+husbyggnad"
        best: list[str] | None = None
        for i in range(len(word) - self._min_part_len, self._min_part_len - 1, -1):
            prefix = word[:i]
            if prefix not in self._words:
                continue

            remainder = word[i:]

            # Try with and without joiners
            for joiner in self._JOINERS:
                if joiner and remainder.startswith(joiner):
                    rest = remainder[len(joiner):]
                else:
                    if joiner:
                        continue
                    rest = remainder

                if not rest:
                    continue

                # Is the rest a word?
                if rest in self._words:
                    candidate = [prefix, rest]
                    # Prefer fewest parts, then longest first part
                    if best is None or len(candidate) < len(best):
                        best = candidate
                    continue

                # Try splitting the rest recursively
                sub = self._try_split(rest, depth + 1)
                if sub:
                    candidate = [prefix] + sub
                    if best is None or len(candidate) < len(best):
                        best = candidate

            # If we found a 2-part split with longest prefix, that's optimal
            if best and len(best) == 2:
                return best

        return best

    def is_valid_compound(self, word: str) -> bool:
        """Check if a word is a valid compound."""
        return self.split(word).is_compound


# Basic Swedish words for fallback (no external file needed)
_BUILTIN_WORDS = {
    # Common nouns
    "barn", "bil", "bok", "bord", "brev", "bro", "dag", "dator", "del",
    "djur", "dörr", "fisk", "flyg", "folk", "fot", "färg", "förening",
    "gata", "glas", "golv", "gård", "hand", "hem", "hjul", "hund", "hus",
    "hår", "jord", "katt", "klass", "klocka", "konst", "kraft", "kropp",
    "kung", "kvinna", "källa", "lag", "land", "ljus", "luft", "lägenhet",
    "man", "mat", "mark", "mor", "musik", "natt", "namn", "nyckel",
    "ord", "papper", "plats", "polis", "program", "rum", "rätt",
    "sjö", "skog", "skola", "sol", "stad", "stol", "ström", "system",
    "tak", "tid", "trafik", "trä", "vagn", "vakt", "vatten", "vin",
    "vind", "väg", "vägg", "värld", "växt", "yta", "öga", "öra",
    # Buildings & places
    "bana", "bank", "butik", "fabrik", "hus", "kyrka", "plan",
    "sjukhus", "station", "torget", "tunnel",
    # Compound-common nouns
    "boll", "brand", "bruk", "by", "båt", "flod", "flyg", "hamn",
    "hyra", "is", "järn", "krig", "kust", "köp", "leda", "mot",
    "park", "resa", "ring", "sand", "sjuk", "snö", "sång", "torg",
    "tåg", "vapen", "vård",
    # Sports & activities
    "fotboll", "handboll", "ishockey", "tennis",
    # Government & society
    "riksdag", "kommun", "ledamot", "minister", "samhälle", "stat",
    # Transport
    "flyg", "järnväg", "spår", "tåg", "tunnel", "buss",
    # Common adjectives
    "stor", "liten", "ny", "gammal", "ung", "lång", "kort", "bred",
    "hög", "låg", "varm", "kall", "vit", "svart", "röd", "blå", "grön",
    "snabb", "sen", "fin", "ren", "fri",
    # Common verbs (stem)
    "lek", "spel", "skriv", "läs", "kör", "spring", "tänk", "sov",
    "sjung", "flytt", "bygg", "städ", "lär", "säg",
    # Body parts
    "arm", "ben", "finger", "huvud", "mage", "rygg", "tand",
    # Nature
    "berg", "blad", "blomma", "eld", "frukt", "gren", "sten", "träd",
    # House/building
    "dörr", "fönster", "golv", "kök", "rum", "trapp", "vägg",
    "byggnad", "våning",
    # Tech
    "data", "fil", "kod", "nät", "webb", "server", "skärm",
    # More common compound parts (prefixes)
    "arbets", "efter", "flyg", "folk", "fot", "före", "grupp", "halv",
    "huvud", "inne", "järn", "lands", "mellan", "mitt", "natt", "riks",
    "sam", "sjuk", "slut", "snö", "sol", "stats", "stor", "trafik",
    "tunnel", "under", "ute", "över",
}
