"""Swedish↔English dictionary lookup based on Folkets lexikon."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class LookupResult:
    """A dictionary lookup result."""
    word: str
    translations: list[str]
    found: bool


class SwedishLexicon:
    """Swedish→English dictionary from Folkets lexikon (36k entries).
    
    Usage:
        lex = SwedishLexicon()
        result = lex.lookup("hund")
        # → LookupResult(word="hund", translations=["dog"], found=True)
        
        results = lex.search("bil")
        # → all words starting with "bil": bil, bildäck, bilkörning, ...
    """

    def __init__(self):
        self._dict: dict[str, list[str]] = {}
        self._load()

    def _load(self):
        tsv_path = Path(__file__).parent.parent / "data" / "folkets_sv_en.tsv"
        if not tsv_path.exists():
            return
        for line in tsv_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or "\t" not in line:
                continue
            sv, en = line.split("\t", 1)
            self._dict[sv.strip()] = [t.strip() for t in en.split(",")]

    def lookup(self, word: str) -> LookupResult:
        """Look up a Swedish word and get English translations."""
        key = word.lower().strip()
        if key in self._dict:
            return LookupResult(word=word, translations=self._dict[key], found=True)
        return LookupResult(word=word, translations=[], found=False)

    def search(self, prefix: str, limit: int = 20) -> list[LookupResult]:
        """Find all words starting with prefix."""
        prefix = prefix.lower().strip()
        results = []
        for sv, ens in self._dict.items():
            if sv.startswith(prefix):
                results.append(LookupResult(word=sv, translations=ens, found=True))
                if len(results) >= limit:
                    break
        return results

    def reverse_lookup(self, english: str, limit: int = 20) -> list[LookupResult]:
        """Find Swedish words that translate to a given English word."""
        eng_lower = english.lower().strip()
        results = []
        for sv, ens in self._dict.items():
            if any(eng_lower in e.lower() for e in ens):
                results.append(LookupResult(word=sv, translations=ens, found=True))
                if len(results) >= limit:
                    break
        return results

    @property
    def size(self) -> int:
        return len(self._dict)
