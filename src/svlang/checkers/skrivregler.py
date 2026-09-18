"""Svenska skrivregler — detect common Swedish writing errors.

Based on:
- Myndigheternas skrivregler (Språkrådet/ISOF)
- Svenska skrivregler (SIS)
- prefix.nu/stavning
- Common errors found in translation work

Categories:
1. Särskrivning (incorrect word splitting)
2. De/dem confusion
3. Common misspellings (svårstavade ord)
4. Double/single consonant errors
5. Punctuation and formatting
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SkrivregelIssue:
    """A detected writing rule violation."""
    rule: str       # category: sarskrivning, dedem, stavfel, interpunktion, dubbelkonsonant
    word: str       # the problematic word/phrase
    suggestion: str # correction
    context: str    # surrounding text
    position: int   # char offset
    line: int = 0   # line number (if available)


# ── Särskrivning patterns ──────────────────────────────────────────
# Common compound words that are often incorrectly split.
# Format: "wrong split" → "correct compound"
_SARSKRIVNINGAR: dict[str, str] = {
    # IT/tech
    "data bas": "databas",
    "data baser": "databaser",
    "data basen": "databasen",
    "fil namn": "filnamn",
    "fil namnet": "filnamnet",
    "fil system": "filsystem",
    "fil systemet": "filsystemet",
    "käll kod": "källkod",
    "käll koden": "källkoden",
    "program vara": "programvara",
    "program varan": "programvaran",
    "nät verk": "nätverk",
    "nät verket": "nätverket",
    "lösen ord": "lösenord",
    "lösen ordet": "lösenordet",
    "an slutning": "anslutning",
    "an slutningen": "anslutningen",
    "av brott": "avbrott",
    "av brottet": "avbrottet",
    "bak grund": "bakgrund",
    "bak grunden": "bakgrunden",
    "bok märke": "bokmärke",
    "bok märket": "bokmärket",
    "in ställning": "inställning",
    "in ställningar": "inställningar",
    "tangent bord": "tangentbord",
    "tangent bordet": "tangentbordet",
    "skriv bord": "skrivbord",
    "skriv bordet": "skrivbordet",
    "skärm släckare": "skärmsläckare",
    "skärm bild": "skärmbild",
    "skärm bilden": "skärmbilden",
    "server rum": "serverrum",
    "server rummet": "serverrummet",
    "upp koppling": "uppkoppling",
    "upp kopplingen": "uppkopplingen",
    "webb läsare": "webbläsare",
    "webb läsaren": "webbläsaren",
    "webb sida": "webbsida",
    "webb sidan": "webbsidan",
    "webb plats": "webbplats",
    "webb platsen": "webbplatsen",
    "e post": "e-post",
    "e posten": "e-posten",
    # Common everyday
    "bil däck": "bildäck",
    "blod tryck": "blodtryck",
    "bröd rost": "brödrost",
    "disk maskin": "diskmaskin",
    "hand duk": "handduk",
    "hand duken": "handduken",
    "hem sida": "hemsida",
    "hus djur": "husdjur",
    "köks bord": "köksbord",
    "mat varor": "matvaror",
    "motor väg": "motorväg",
    "natt duksbord": "nattduksbord",
    "skol gård": "skolgård",
    "slut station": "slutstation",
    "sov rum": "sovrum",
    "sov rummet": "sovrummet",
    "tand borste": "tandborste",
    "tvätl maskin": "tvättmaskin",
    "tvält maskin": "tvättmaskin",
    "tvätt maskin": "tvättmaskin",
    "vatten kran": "vattenkran",
    # Abstract/admin
    "arbets plats": "arbetsplats",
    "arbets platsen": "arbetsplatsen",
    "fel meddelande": "felmeddelande",
    "fel meddelandet": "felmeddelandet",
    "för slag": "förslag",
    "för slaget": "förslaget",
    "för utsättning": "förutsättning",
    "för utsättningar": "förutsättningar",
    "höger klick": "högerklick",
    "höger klicka": "högerklicka",
    "miljö vänlig": "miljövänlig",
    "ord lista": "ordlista",
    "ord listan": "ordlistan",
    "rättstavnings kontroll": "rättstavningskontroll",
    "slut giltig": "slutgiltig",
    "slut giltigt": "slutgiltigt",
    "standard inställning": "standardinställning",
    "standard inställningar": "standardinställningar",
    "system krav": "systemkrav",
    "system kraven": "systemkraven",
    "tids zon": "tidszon",
    "tids zonen": "tidszonen",
    "upphovs rätt": "upphovsrätt",
    "upphovs rätten": "upphovsrätten",
    "var dag": "vardag",
    "var dagen": "vardagen",
    "över sättning": "översättning",
    "över sättningar": "översättningar",
    "över sättare": "översättare",
}

# ── Common misspellings ────────────────────────────────────────────
# Based on prefix.nu/stavning and Språkrådet
_STAVFEL: dict[str, str] = {
    # Double/single consonant
    "nogrann": "noggrann",
    "vilkor": "villkor",
    "mäniska": "människa",
    "mäniskor": "människor",
    "tyvär": "tyvärr",
    "synns": "syns",
    "allmänn": "allmän",
    "abonemang": "abonnemang",
    "sattelit": "satellit",
    "hittils": "hittills",
    "intreserad": "intresserad",
    "genomskinnlig": "genomskinlig",
    "kollosal": "kolossal",
    "imun": "immun",
    "rennäsans": "renässans",
    "konkurera": "konkurrera",
    "skillsmässa": "skilsmässa",
    "medlemsskap": "medlemskap",
    "modersspråk": "moderspråk",
    "oförätt": "oförrätt",
    "arbetssam": "arbetsam",
    "skottsk": "skotsk",
    "olyckssalig": "olycksalig",
    # I/E confusion
    "defenitivt": "definitivt",
    "defenitivt": "definitivt",
    "ingridiens": "ingrediens",
    "ingridiensr": "ingredienser",
    "igentligen": "egentligen",
    "medecin": "medicin",
    "pessemistisk": "pessimistisk",
    "neglegera": "negligera",
    "epedemi": "epidemi",
    "kontenuerlig": "kontinuerlig",
    "insperera": "inspirera",
    # E/A confusion
    "parantes": "parentes",
    "konkurrans": "konkurrens",
    "almenacka": "almanacka",
    "diligans": "diligens",
    "konferans": "konferens",
    # Missing vowel
    "orginal": "original",
    "matrial": "material",
    "religös": "religiös",
    "agusti": "augusti",
    "exprimentera": "experimentera",
    # Missing consonant
    "poträtt": "porträtt",
    "repotage": "reportage",
    "kuver": "kuvert",
    "konser": "konsert",
    "kvartalvinst": "kvartalsvinst",
    "giftemål": "giftermål",
    # Extra consonant (inbillade)
    "följdaktligen": "följaktligen",
    "intervjuva": "intervjua",
    "skiljd": "skild",
    "öppenhjärtlig": "öppenhjärtig",
    "jämnlik": "jämlik",
    "entydlig": "entydig",
    "låneord": "lånord",
    "krigsföring": "krigföring",
    "manusskript": "manuskript",
    "själslös": "själlös",
    "himmelsriket": "himmelriket",
    "fadersmord": "fadermord",
    "tidstagning": "tidtagning",
    "tidspunkt": "tidpunkt",
    "betygssätta": "betygsätta",
    "skogsvaktare": "skogvaktare",
    # English-influenced
    "shampoo": "schampo",
    "casino": "kasino",
    # Common everyday typos
    # "idag/igår/imorgon" — båda former accepteras (SAOL), skippar
    "isåfall": "i så fall",
    "iväg": "i väg",
    # "ifrån" removed — valid Swedish (därifrån, härifrån, etc.)
    "tillochmed": "till och med",
    "vokal": None,  # OK, many meanings
}

# Filter None
STAVFEL = {k: v for k, v in _STAVFEL.items() if v is not None}

# ── De/dem patterns ────────────────────────────────────────────────
# Patterns that are almost always wrong:
#   "dem" as subject → should be "de"
#   "de" as object → should be "dem"
# Note: This is very hard to do perfectly without a full parser,
# so we use high-confidence heuristics only.

# "dem" as subject at sentence start → likely should be "de"
# Only flag at start of sentence (after . ! ? \n or start of text) + verb
# This avoids false positives like "Reta dem inte!" where dem is object
_DEM_AS_SUBJECT = re.compile(
    r'(?:^|[.!?\n]\s*)(?:Dem|dem)\s+'
    r'(?:är|var|har|hade|ska|skall|skulle|kan|kunde|måste|bör|'
    r'vill|ville|kommer|gör|gjorde|går|gick|tycker|tror|'
    r'behöver|verkar|brukar|försöker|börjar|slutar)\b',
    re.MULTILINE,
)

# NOTE: "preposition + de" removed — too many false positives.
# "för de korta", "av de valda" etc. use "de" as determiner (correct).
# Only flagging "de" as pronoun requires full parsing.

# "ge/gav/gett de" (indirect object) → "dem" — HIGH confidence
# Only when "de" is followed by end-of-sentence or another pronoun/determiner
_DE_INDIRECT_OBJECT = re.compile(
    r'\b(?:ge|gav|gett|ger|visa|visade|berätta|berättade|'
    r'skicka|skickade|lämna|lämnade)\s+de\s*[.!?,;:\n]',
    re.IGNORECASE,
)

# ── Punctuation patterns ──────────────────────────────────────────
# Common punctuation errors in Swedish

# Multiple spaces
_DOUBLE_SPACE = re.compile(r'(?<!\n)  (?!\n)')  # Not at line starts

# Missing space after punctuation
_MISSING_SPACE_AFTER = re.compile(r'[.!?,:;][A-ZÅÄÖ]')

# Space before punctuation (except open parens)
_SPACE_BEFORE_PUNCT = re.compile(r'\s+[.!?,;:](?!\w)')


class SkrivreglerChecker:
    """Detect common Swedish writing errors.
    
    Usage:
        checker = SkrivreglerChecker()
        issues = checker.check("Jag har en data bas som dem har skapat")
        # → [SkrivregelIssue(rule="sarskrivning", word="data bas", ...),
        #    SkrivregelIssue(rule="dedem", word="dem har", ...)]
    """

    def __init__(
        self,
        *,
        check_sarskrivning: bool = True,
        check_dedem: bool = True,
        check_stavfel: bool = True,
        check_interpunktion: bool = False,  # Opt-in: too noisy for PO files
    ):
        self._check_sarskrivning = check_sarskrivning
        self._check_dedem = check_dedem
        self._check_stavfel = check_stavfel
        self._check_interpunktion = check_interpunktion
        
        # Build särskrivning pattern (case-insensitive, longest first)
        if check_sarskrivning:
            escaped = [re.escape(t) for t in sorted(_SARSKRIVNINGAR, key=len, reverse=True)]
            self._sarskrivning_pattern = re.compile(
                r'\b(' + '|'.join(escaped) + r')\b',
                re.IGNORECASE,
            )
        
        # Build stavfel pattern
        if check_stavfel:
            escaped = [re.escape(t) for t in sorted(STAVFEL, key=len, reverse=True)]
            self._stavfel_pattern = re.compile(
                r'\b(' + '|'.join(escaped) + r')\b',
                re.IGNORECASE,
            )

    def _context(self, text: str, start: int, end: int) -> str:
        """Extract context around a match."""
        s = max(0, start - 30)
        e = min(len(text), end + 30)
        return text[s:e]

    def _line_number(self, text: str, pos: int) -> int:
        """Get 1-based line number for a position."""
        return text[:pos].count('\n') + 1

    def check(self, text: str) -> list[SkrivregelIssue]:
        """Find writing rule issues in text."""
        issues: list[SkrivregelIssue] = []

        # ── Särskrivning ──
        if self._check_sarskrivning:
            for m in self._sarskrivning_pattern.finditer(text):
                found = m.group(0)
                # Skip if either word is ALL CAPS (likely a placeholder: fil NAMN)
                parts = found.split()
                if any(p.isupper() and len(p) > 1 for p in parts):
                    continue
                key = found.lower()
                # In "den N:e posten" the e belongs to an ordinal suffix,
                # not to a split spelling of e-post.
                if key.startswith('e ') and re.search(r'\b(?:\d+|[A-ZÅÄÖ]):$', text[:m.start()]):
                    continue
                correction = _SARSKRIVNINGAR.get(key, "")
                if correction:
                    issues.append(SkrivregelIssue(
                        rule="sarskrivning",
                        word=found,
                        suggestion=correction,
                        context=self._context(text, m.start(), m.end()),
                        position=m.start(),
                        line=self._line_number(text, m.start()),
                    ))

        # ── De/dem ──
        if self._check_dedem:
            for m in _DEM_AS_SUBJECT.finditer(text):
                issues.append(SkrivregelIssue(
                    rule="dedem",
                    word=m.group(0).strip(),
                    suggestion='"dem" som subjekt → bör vara "de"',
                    context=self._context(text, m.start(), m.end()),
                    position=m.start(),
                    line=self._line_number(text, m.start()),
                ))
            
            for m in _DE_INDIRECT_OBJECT.finditer(text):
                issues.append(SkrivregelIssue(
                    rule="dedem",
                    word=m.group(0).strip(),
                    suggestion='"de" som indirekt objekt → bör vara "dem"',
                    context=self._context(text, m.start(), m.end()),
                    position=m.start(),
                    line=self._line_number(text, m.start()),
                ))

        # ── Stavfel ──
        if self._check_stavfel:
            for m in self._stavfel_pattern.finditer(text):
                found = m.group(0)
                key = found.lower()
                correction = STAVFEL.get(key, "")
                if correction:
                    issues.append(SkrivregelIssue(
                        rule="stavfel",
                        word=found,
                        suggestion=correction,
                        context=self._context(text, m.start(), m.end()),
                        position=m.start(),
                        line=self._line_number(text, m.start()),
                    ))

        # ── Interpunktion ──
        if self._check_interpunktion:
            for m in _DOUBLE_SPACE.finditer(text):
                issues.append(SkrivregelIssue(
                    rule="interpunktion",
                    word="  ",
                    suggestion="Dubbelt mellanslag → enkelt",
                    context=self._context(text, m.start(), m.end()),
                    position=m.start(),
                    line=self._line_number(text, m.start()),
                ))

        issues.sort(key=lambda i: i.position)
        return issues

    @property
    def rule_counts(self) -> dict[str, int]:
        """Number of patterns per rule category."""
        return {
            "sarskrivning": len(_SARSKRIVNINGAR),
            "stavfel": len(STAVFEL),
            "dedem": 3,  # 3 pattern groups
            "interpunktion": 1,  # double space
        }
