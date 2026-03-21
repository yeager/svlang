"""Swedish naturalness heuristics for detecting machine translation."""

from __future__ import annotations

import re
from typing import NamedTuple

try:
    import stanza
    STANZA_AVAILABLE = True
except ImportError:
    STANZA_AVAILABLE = False


class NaturalnessIssue(NamedTuple):
    """An issue that affects naturalness."""
    category: str  # "length", "word_order", "passive", "anglicism"
    description: str
    severity: float  # 0.0-1.0, higher = more problematic
    context: str = ""


class NaturalnessResult(NamedTuple):
    """Result from naturalness analysis."""
    score: float  # 0-10, 10 = perfectly natural
    issues: list[NaturalnessIssue]
    sentence_count: int
    avg_sentence_length: float
    passive_ratio: float
    anglicism_count: int


class SwedishNaturalness:
    """Analyze Swedish text naturalness using linguistic heuristics."""
    
    def __init__(self):
        self.stanza_nlp = None
        if STANZA_AVAILABLE:
            try:
                self.stanza_nlp = stanza.Pipeline('sv', processors='tokenize,pos', verbose=False)
            except Exception:
                pass  # Fallback to rule-based
        
        # Common anglicisms that have Swedish alternatives
        self.anglicisms = {
            "feedback": "återkoppling",
            "implementera": "genomföra",
            "fokusera": "fokusera på/koncentrera sig på",
            "involvera": "involvera/inkludera",
            "allokera": "tilldela",
            "prioritera": "prioritera/sätta i första hand",
            "optimera": "förbättra/optimera",
            "integrerad": "integrerad/sammanbyggd",
            "kommunicera": "kommunicera/meddela",
            "identifiera": "identifiera/fastställa",
            "attackera": "angripa",
            "supporta": "stödja",
            "uppdatera": "uppdatera/förnya",
            "defaultvärde": "standardvärde",
            "performance": "prestanda",
            "feature": "funktion/egenskap",
            "issue": "problem",
            "outputen": "resultatet/utskriften",
            "inputen": "indata/inmatningen",
            "deadline": "tidsfrist",
            "meeting": "möte",
            "workshop": "arbetsgrupp",
            "timeline": "tidsplan",
            "upgrade": "uppgradering",
            "backup": "säkerhetskopia",
            "database": "databas",
            "interface": "gränssnitt",
        }
        
        # Swedish passive indicators
        self.passive_indicators = [
            "blev", "blir", "blivit", "har blivit", "hade blivit",
            "gjordes", "görs", "gjorts", "har gjorts", "hade gjorts",
            "skapades", "skapas", "skapats", "har skapats",
            "användes", "används", "använts", "har använts",
            "implementerades", "implementeras", "implementerats"
        ]
    
    def _simple_pos_tag(self, sentence: str) -> list[tuple[str, str]]:
        """Simple rule-based POS tagging fallback."""
        words = re.findall(r'\b\w+\b', sentence.lower())
        tagged = []
        
        for word in words:
            # Very basic Swedish POS rules
            if word in ["och", "eller", "men", "utan", "för", "så"]:
                pos = "CCONJ"  # Coordinating conjunction
            elif word in ["att", "som", "när", "eftersom", "medan", "om"]:
                pos = "SCONJ"  # Subordinating conjunction  
            elif word in ["är", "var", "blir", "blev", "har", "hade", "ska", "skulle"]:
                pos = "VERB"
            elif word in ["det", "den", "de", "detta", "denna", "dessa"]:
                pos = "PRON"
            elif word.endswith(("a", "ar", "or", "er", "an", "en", "on")):
                pos = "NOUN"  # Likely noun
            elif word.endswith(("ade", "de", "te", "dde")):
                pos = "VERB"  # Past tense verb
            elif word.endswith("t") and len(word) > 3:
                pos = "ADJ"   # Neuter adjective
            else:
                pos = "X"     # Unknown
                
            tagged.append((word, pos))
        
        return tagged
    
    def _check_v2_rule(self, sentence: str) -> bool:
        """Check if sentence follows Swedish V2 (verb second) rule."""
        if self.stanza_nlp:
            try:
                doc = self.stanza_nlp(sentence)
                if doc.sentences:
                    sent = doc.sentences[0]
                    words = [(w.text, w.upos) for w in sent.words]
                else:
                    words = self._simple_pos_tag(sentence)
            except Exception:
                words = self._simple_pos_tag(sentence)
        else:
            words = self._simple_pos_tag(sentence)
        
        if len(words) < 2:
            return True  # Too short to violate V2
        
        # Look for main verb in position 2 (after potential subject/adverbial)
        verb_positions = [i for i, (word, pos) in enumerate(words) if pos == "VERB"]
        
        if not verb_positions:
            return True  # No verb found
        
        # In main clauses, verb should typically be in position 1-3
        first_verb_pos = verb_positions[0]
        return first_verb_pos <= 2
    
    def _count_passive_constructions(self, text: str) -> int:
        """Count passive voice constructions."""
        text_lower = text.lower()
        passive_count = 0
        
        for indicator in self.passive_indicators:
            passive_count += text_lower.count(indicator)
        
        return passive_count
    
    def _find_anglicisms(self, text: str) -> list[str]:
        """Find anglicisms in text."""
        text_lower = text.lower()
        found_anglicisms = []
        
        for anglicism in self.anglicisms:
            if re.search(r'\b' + re.escape(anglicism) + r'\b', text_lower):
                found_anglicisms.append(anglicism)
        
        return found_anglicisms
    
    def _analyze_sentence_structure(self, text: str) -> tuple[int, float, list[NaturalnessIssue]]:
        """Analyze sentence structure and identify issues."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        issues = []
        word_counts = []
        
        for i, sentence in enumerate(sentences):
            words = re.findall(r'\b\w+\b', sentence)
            word_count = len(words)
            word_counts.append(word_count)
            
            # Check for very long sentences (machine translation indicator)
            if word_count > 40:
                issues.append(NaturalnessIssue(
                    category="length",
                    description=f"Mycket lång mening ({word_count} ord) kan tyda på maskinöversättning",
                    severity=min(1.0, (word_count - 40) / 20),
                    context=sentence[:100] + "..." if len(sentence) > 100 else sentence
                ))
            
            # Check V2 rule
            if not self._check_v2_rule(sentence):
                issues.append(NaturalnessIssue(
                    category="word_order",
                    description="Möjlig överträdelse av V2-regeln (verbet borde vara andrä satsdelen)",
                    severity=0.6,
                    context=sentence[:100] + "..." if len(sentence) > 100 else sentence
                ))
        
        avg_length = sum(word_counts) / len(word_counts) if word_counts else 0
        return len(sentences), avg_length, issues
    
    def analyze(self, text: str) -> NaturalnessResult:
        """Analyze text naturalness and return score with issues."""
        if not text.strip():
            return NaturalnessResult(10.0, [], 0, 0.0, 0.0, 0)
        
        # Analyze sentence structure
        sentence_count, avg_length, structure_issues = self._analyze_sentence_structure(text)
        
        # Count passive constructions
        passive_count = self._count_passive_constructions(text)
        word_count = len(re.findall(r'\b\w+\b', text))
        passive_ratio = passive_count / max(1, word_count) if word_count > 0 else 0
        
        # Find anglicisms
        anglicisms = self._find_anglicisms(text)
        
        all_issues = structure_issues[:]
        
        # Add passive voice issues
        if passive_ratio > 0.05:  # More than 5% passive constructions
            all_issues.append(NaturalnessIssue(
                category="passive",
                description=f"Hög andel passiva konstruktioner ({passive_ratio:.1%}) kan tyda på maskinöversättning",
                severity=min(1.0, passive_ratio * 10),
                context=""
            ))
        
        # Add anglicism issues
        for anglicism in anglicisms:
            suggestion = self.anglicisms[anglicism]
            all_issues.append(NaturalnessIssue(
                category="anglicism",
                description=f"Anglicism '«{anglicism}»' → förslag: {suggestion}",
                severity=0.4,
                context=""
            ))
        
        # Calculate overall naturalness score (0-10)
        base_score = 10.0
        
        # Penalize based on issues
        for issue in all_issues:
            base_score -= issue.severity * 2.0
        
        # Additional penalties for statistical patterns
        if avg_length > 25:
            base_score -= 1.0
        if passive_ratio > 0.1:
            base_score -= 1.5
        
        # Ensure score is in valid range
        final_score = max(0.0, min(10.0, base_score))
        
        return NaturalnessResult(
            score=final_score,
            issues=all_issues,
            sentence_count=sentence_count,
            avg_sentence_length=avg_length,
            passive_ratio=passive_ratio,
            anglicism_count=len(anglicisms)
        )