"""Svengelska detector — flag unnecessary anglicisms in Swedish text."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Anglicism:
    """A detected anglicism with a suggested Swedish alternative."""
    word: str
    suggestion: str
    context: str  # surrounding text
    position: int  # char offset


# Common anglicisms with Swedish alternatives.
# Based on Språkrådet recommendations and common translation pitfalls.
_ANGLICISMS: dict[str, str] = {
    # Verbs
    "implementera": "genomföra, införa",
    "initiera": "inleda, starta",
    "adressera": "ta itu med, hantera",
    "facilitera": "underlätta",
    "monitorera": "övervaka",
    "trigga": "utlösa, sätta igång",
    "briffa": "informera, instruera",
    "mejla": "e-posta, skicka e-post",
    "googla": "söka på nätet",
    "cancelera": "avboka, ställa in",
    "cancella": "avboka, ställa in",
    "benchmarka": "jämföra, mäta",
    "brainstorma": "idésamla",
    "busta": "spränga, bryta",
    "chilla": "koppla av, ta det lugnt",
    "churna": "tappa kunder",
    "converta": "omvandla, konvertera",
    "delivera": "leverera",
    "dippa": "doppa, sjunka",
    "escalera": "eskalera, trappa upp",
    "fetcha": "hämta",
    "flusha": "spola, tömma",
    "forwarda": "vidarebefordra",
    "launcha": "lansera",
    "lägga upp en story": "publicera",
    "merga": "sammanfoga, slå ihop",
    "pitcha": "presentera, sälja in",
    "pusha": "driva på, trycka på",
    "rendera": "återge, framställa",
    "reseta": "återställa",
    "reviewera": "granska",
    "scrolla": "bläddra, rulla",
    "skipa": "hoppa över",
    "sparka av": "starta, dra igång",
    "streama": "strömma, sända",
    "swipa": "svepa",
    "tagga": "märka, märka upp",
    "trenda": "vara populär",
    "uppdatera": None,  # OK — established Swedish
    "uppgradera": None,  # OK — established

    # Nouns
    "approach": "tillvägagångssätt, metod",
    "awareness": "medvetenhet, kännedom",
    "backup": "säkerhetskopia",
    "benchmark": "riktmärke, jämförelse",
    "best practice": "bästa praxis, god praxis",
    "blocker": "hinder",
    "brainstorm": "idésamling",
    "brief": "instruktion, uppdrag",
    "budget": None,  # OK — established
    "case": "fall, ärende",
    "challenge": "utmaning",
    "deadline": "tidsfrist, slutdatum",
    "feature": "funktion, egenskap",
    "feedback": "återkoppling, respons",
    "flow": "flöde",
    "gap": "glapp, lucka",
    "high-level": "övergripande",
    "impact": "påverkan, inverkan",
    "input": "synpunkter, underlag",
    "insight": "insikt",
    "issue": "fråga, problem",
    "item": "punkt, sak",
    "key takeaway": "viktigaste slutsatsen",
    "leverage": "utnyttja, dra nytta av",
    "mindset": "tankesätt, inställning",
    "outcome": "resultat, utfall",
    "output": "resultat, utdata",
    "pain point": "smärtpunkt, problem",
    "performance": "prestanda, resultat",
    "pipeline": "kedja, process",
    "pitch": "presentation, säljpitch",
    "scope": "omfattning, räckvidd",
    "setup": "uppställning, konfiguration",
    "stakeholder": "intressent",
    "startup": "nystartad, uppstart",
    "target": "mål, målgrupp",
    "task": "uppgift",
    "team": None,  # OK — established
    "template": "mall",
    "timeline": "tidslinje, tidsplan",
    "tool": "verktyg",
    "touchpoint": "kontaktpunkt",
    "trade-off": "avvägning",
    "trigger": "utlösare",
    "update": "uppdatering",
    "workshop": None,  # OK — established

    # Adjectives
    "agil": "smidig, flexibel",
    "aligned": "samstämd, i linje",
    "customized": "anpassad, skräddarsydd",
    "dedicated": "engagerad, tillägnad",
    "hands-on": "praktisk, handgriplig",
    "key": "viktig, central",
    "lean": "resurssnål, slimmad",
    "on track": "på rätt spår, i fas",
    "proaktiv": "förebyggande, framåtblickande",
    "senior": "erfaren, ledande",
    "sustainable": "hållbar",
    "transparent": None,  # OK — established
}

# Filter out None (accepted words)
ANGLICISMS = {k: v for k, v in _ANGLICISMS.items() if v is not None}


class SvengelskaChecker:
    """Detect unnecessary anglicisms in Swedish text.
    
    Usage:
        checker = SvengelskaChecker()
        hits = checker.check("Vi behöver implementera en ny approach")
        # → [Anglicism("implementera", "genomföra, införa", ...),
        #    Anglicism("approach", "tillvägagångssätt, metod", ...)]
    """

    # Swedish inflection suffixes to strip when matching
    # Order matters: longest first
    _SUFFIXES = (
        "erade", "erades",       # -era verbs past: implementerade
        "ering",                 # noun from -era verb: implementering
        "erna", "arna", "orna",  # plural definite
        "erar",                  # -era verbs present: implementerar
        "erat",                  # -era verbs supine: implementerat
        "ande",                  # present participle
        "ades",                  # past passive
        "ers", "ens", "ets",    # genitive
        "ade",                   # past tense
        "ar", "er", "or",       # plural
        "en", "et", "an",       # definite
        "at", "ad",             # supine / past participle
        "s",                     # genitive / plural
    )

    def __init__(self, *, extra_terms: dict[str, str] | None = None):
        self._terms = dict(ANGLICISMS)
        if extra_terms:
            self._terms.update(extra_terms)
        # Build regex pattern — sort by length (longest first) for greedy match
        escaped = [re.escape(t) for t in sorted(self._terms, key=len, reverse=True)]
        self._pattern = re.compile(
            r'\b(' + '|'.join(escaped) + r')\b',
            re.IGNORECASE,
        )
        # Also build a set for fast stem lookup
        self._term_set = {t.lower() for t in self._terms}

    def _stem_match(self, word: str) -> str | None:
        """Try to match a word to a known anglicism by stripping suffixes."""
        low = word.lower()
        if low in self._term_set:
            return low
        for suffix in self._SUFFIXES:
            if low.endswith(suffix) and len(low) > len(suffix) + 2:
                stem = low[:-len(suffix)]
                if stem in self._term_set:
                    return stem
                # Try adding back common verb ending: implementer → implementera
                if (stem + "a") in self._term_set:
                    return stem + "a"
        return None

    def check(self, text: str) -> list[Anglicism]:
        """Find anglicisms in text."""
        hits = []
        seen_positions: set[int] = set()

        # First pass: exact pattern matches
        for m in self._pattern.finditer(text):
            word = m.group(0)
            key = word.lower()
            suggestion = self._terms.get(key, "")
            if not suggestion:
                suggestion = self._terms.get(word, "")
            if suggestion:
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 30)
                context = text[start:end]
                hits.append(Anglicism(
                    word=word, suggestion=suggestion,
                    context=context, position=m.start(),
                ))
                seen_positions.add(m.start())

        # Second pass: check inflected forms (word boundaries)
        for m in re.finditer(r'\b(\w+)\b', text):
            if m.start() in seen_positions:
                continue
            stem = self._stem_match(m.group(0))
            if stem:
                suggestion = self._terms[stem]
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 30)
                context = text[start:end]
                hits.append(Anglicism(
                    word=m.group(0), suggestion=suggestion,
                    context=context, position=m.start(),
                ))

        hits.sort(key=lambda h: h.position)
        return hits

    @property
    def term_count(self) -> int:
        return len(self._terms)
