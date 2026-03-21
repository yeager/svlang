"""Swedish word frequency analysis."""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple


class FrequencyResult(NamedTuple):
    """Result from frequency analysis."""
    word: str
    frequency_score: float  # 0.0 = most common, 1.0 = very rare/unknown
    found: bool
    rank: int | None  # Position in frequency list (1-based), None if not found


class SwedishFrequency:
    """Swedish word frequency analyzer using top 10k word list."""
    
    def __init__(self):
        self._load_frequency_data()
    
    def _load_frequency_data(self):
        """Load frequency data from built-in word list."""
        data_dir = Path(__file__).parent.parent / "data"
        wordlist_path = data_dir / "sv_frequency_10k.txt"
        
        # If our curated frequency list doesn't exist, create it from the wordlist
        if not wordlist_path.exists():
            self._create_frequency_list(wordlist_path)
        
        self.word_to_rank = {}
        self.total_words = 0
        
        with wordlist_path.open(encoding="utf-8") as f:
            for rank, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith("#"):
                    word = line.lower()
                    self.word_to_rank[word] = rank
                    self.total_words = rank
    
    def _create_frequency_list(self, output_path: Path):
        """Create a frequency list from the existing wordlist."""
        # This is a simplified approach - we'll just take the first 10k most common words
        # In a real implementation, you'd use actual frequency data from corpora
        data_dir = Path(__file__).parent.parent / "data"
        wordlist_path = data_dir / "sv_wordlist.txt"
        
        common_words = [
            # Most common Swedish words (manually curated based on linguistic knowledge)
            "och", "i", "att", "det", "som", "för", "på", "är", "av", "en",
            "till", "med", "har", "de", "inte", "var", "från", "den", "han", "hon",
            "vi", "kan", "om", "så", "skulle", "men", "när", "ett", "här", "bli",
            "bara", "ska", "nu", "ha", "får", "år", "efter", "alla", "två", "mer",
            "göra", "komma", "vid", "över", "andra", "första", "ser", "tid", "många",
            "säga", "innan", "utan", "också", "låta", "enligt", "sätt", "mellan",
            "varje", "eftersom", "redan", "under", "endast", "eller", "hela", "genom",
            "samma", "faktiskt", "inom", "mot", "där", "varför", "vilket", "vad", "hur",
            "ibland", "ju", "helt", "då", "både", "därför", "fram", "nog", "ändå",
            "väl", "precis", "själv", "tre", "fyra", "fem", "sex", "sju", "åtta",
            "nio", "tio", "elva", "tolv", "dag", "vecka", "månad", "kanske", "alltid",
            "aldrig", "någon", "något", "några", "inget", "ingenting", "allting",
            "eftersom", "därför", "medan", "fast", "dock", "ändå", "alltså", "istället",
            # Add more common words
            "behöver", "behöva", "denna", "denna", "våra", "vår", "vara", "finns",
            "finnas", "mycket", "lite", "stor", "stora", "liten", "lilla", "bra", "dålig",
            "ny", "nya", "gamla", "gammal", "första", "sista", "nästa", "förra",
            "kommer", "gå", "går", "gör", "ta", "tar", "tror", "vill", "ville", "veta", "vet",
            "använda", "använder", "system", "problem", "lösning", "projekt", "arbete",
            "arbeta", "jobba", "studera", "lära", "hjälp", "hjälpa", "tänka", "tycker",
            "känna", "höra", "hör", "se", "ser", "visa", "titta", "kolla", "fundera", "räkna",
            # Very common everyday words
            "jag", "mig", "min", "mitt", "mina", "dig", "din", "ditt", "dina", "oss", "er", "ers",
            "hem", "hus", "bil", "mat", "mjölk", "affär", "affären", "köpa", "köper", "äta",
            "äter", "sova", "sover", "jobbar", "arbetar", "lagar", "middag", "frukost",
            "lunch", "morgon", "kväll", "natt", "imorgon", "igår", "idag", "sen", "sedan",
            "klocka", "timme", "minut", "sekund", "pengar", "kosta", "kostar", "pris",
            "familj", "vänner", "barn", "föräldrar", "mamma", "pappa", "syster", "bror",
            "skola", "lärare", "elev", "bok", "läsa", "läser", "skriva", "skriver"
        ]
        
        # Read the full wordlist and take first 10k minus our curated common words
        if wordlist_path.exists():
            with wordlist_path.open(encoding="utf-8") as f:
                all_words = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        word = line.lower()
                        if word not in common_words and word.isalpha():
                            all_words.append(word)
        
        # Create the frequency list
        output_path.parent.mkdir(exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            f.write("# Top 10k Swedish words by frequency (estimated)\n")
            f.write("# Most common words first\n")
            
            # Write our curated common words first
            for word in common_words:
                f.write(f"{word}\n")
            
            # Add the rest up to 10k
            remaining = 10000 - len(common_words)
            for word in all_words[:remaining]:
                f.write(f"{word}\n")
    
    def get_frequency_score(self, word: str) -> FrequencyResult:
        """Get frequency score for a word.
        
        Args:
            word: Word to analyze
            
        Returns:
            FrequencyResult with score (0.0=common, 1.0=rare) and rank info
        """
        word_clean = re.sub(r'[^\w\-]', '', word.lower())
        
        if word_clean in self.word_to_rank:
            rank = self.word_to_rank[word_clean]
            # Convert rank to score: rank 1 = score 0.0, rank 10000 = score 1.0
            score = (rank - 1) / (self.total_words - 1)
            return FrequencyResult(word, score, True, rank)
        else:
            # Word not found = very rare/unknown
            return FrequencyResult(word, 1.0, False, None)
    
    def analyze_text(self, text: str, threshold: float = 0.7) -> list[FrequencyResult]:
        """Analyze text for rare/archaic words.
        
        Args:
            text: Text to analyze
            threshold: Score threshold for flagging (0.7 = fairly uncommon)
            
        Returns:
            List of FrequencyResult for words above threshold
        """
        # Simple tokenization
        words = re.findall(r'\b\w+\b', text.lower())
        
        flagged_words = []
        seen = set()
        
        for word in words:
            if word in seen or len(word) < 3:  # Skip very short words and duplicates
                continue
            seen.add(word)
            
            result = self.get_frequency_score(word)
            if result.frequency_score >= threshold:
                flagged_words.append(result)
        
        # Sort by frequency score (most unusual first)
        return sorted(flagged_words, key=lambda x: x.frequency_score, reverse=True)
    
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
            return "mycket sällsynt/okänt"