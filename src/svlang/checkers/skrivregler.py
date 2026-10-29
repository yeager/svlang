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


STYLE_GUIDE = (
    ("Skiljetecken och skrivtecken", "Citattecken, mellanslag, talintervall och projektets formatprofil kontrolleras automatiskt.", "Bedöm ellips, komma, semikolon, kolon, bindestreck, tankstreck och snedstreck i sitt sammanhang. Komma före och kan vara korrekt mellan huvudsatser eller kring inskott."),
    ("Stor och liten bokstav", "Kontrolleras där formaten ger säkra signaler.", "Bedöm namn, rubriker, organisationer och sammansättningar med namn."),
    ("Sammansättningar", "Vanliga särskrivningar och kända stavfel kontrolleras automatiskt.", "Bedöm nya, fackliga och långa sammansättningar."),
    ("Förkortningar", "Enskilda formatregler kontrolleras när de är säkra.", "Bedöm förkortningens lämplighet, böjning och interpunktion."),
    ("Tal och siffror", "Talgrupper, decimaler, procent och intervall kontrolleras automatiskt.", "Bedöm sifferform, datum, tider, mått, valuta och telefonnummer."),
    ("Citat och repliker", "Otvetydigt engelskt öppningscitat flaggas.", "Bedöm citatets interpunktion, replikform och trohet mot originalet."),
    ("Textens form", "Ingen automatisk strukturdömning görs för korta UI-strängar.", "Bedöm rubriker, stycken, punktlistor, betoning och avstavning."),
)


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
    "över sättning": "översättning",
    "över sättningar": "översättningar",
    "över sättare": "översättare",
}

# ── Common misspellings ────────────────────────────────────────────
# Based on prefix.nu/stavning and Språkrådet
_STAVFEL: dict[str, str] = {
    # Three identical consonants at compound boundaries (Språkrådets frågelåda).
    "adressspecifik": "adresspecifik",
    "adressspecifika": "adresspecifika",
    "processstatus": "processtatus",
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
    # "iväg/i väg" are both accepted spellings (Svensk ordbok).
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
    r'skicka|skickade|lämna|lämnade)\s+de\s*[.!?,;:]',
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

# Swedish typography: no whitespace immediately before punctuation or
# immediately inside ordinary parentheses. Three dots are one ellipsis glyph.
_SPACE_BEFORE_PUNCTUATION = re.compile(r'\S[ \t]+[,.!?;:](?!\w)')
_SPACE_INSIDE_PARENS = re.compile(r'\([ \t]+\S|\S[ \t]+\)')
_ENGLISH_CURLY_QUOTES = re.compile(r'“')
_LARGE_DOTTED_NUMBER = re.compile(r'\b\d{1,3}(?:\.\d{3}){2,}\b')
_IPV4_ADDRESS = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
_PERCENT_WITHOUT_SPACE = re.compile(r'\b\d+(?:,\d+)?%(?!\w)')
_SPACED_NUMERIC_HYPHEN = re.compile(r'\b\d+[ \t]+-[ \t]+\d+\b')


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
                if key.startswith('e ') and re.search(r'\b(?:\d+|[A-ZÅÄÖ][A-ZÅÄÖ0-9_]*):$', text[:m.start()]):
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

            # Flag likely compound spelling errors without automatically
            # rewriting names, abbreviations, code or deliberate repetitions.
            protected = re.compile(r'https?://\S+|www\.\S+|\{[^}]*\}|<[^>]*>|`[^`]*`', re.IGNORECASE)
            spans = [m.span() for m in protected.finditer(text)]
            for m in re.finditer(r'\b[a-zåäö]+\b', text, re.IGNORECASE):
                word = m.group()
                if word.lower() in STAVFEL or word.isupper():
                    continue
                if any(start <= m.start() < end for start, end in spans):
                    continue
                if re.search(r'([bcdfghjklmnpqrstvwxz])\1{2,}', word, re.IGNORECASE):
                    issues.append(SkrivregelIssue(
                        rule="stavfel", word=word,
                        suggestion="Kontrollera tre lika konsonanter i följd",
                        context=self._context(text, m.start(), m.end()),
                        position=m.start(), line=self._line_number(text, m.start()),
                    ))

        # ── Interpunktion ──
        # Comma use is context dependent. In particular, Swedish normally
        # uses a comma between coordinated main clauses, so do not flag every
        # occurrence of 'och'.
        # These formatting checks are high-confidence in ordinary Swedish prose.
        for pattern, suggestion in (
            (_SPACE_BEFORE_PUNCTUATION, 'Ta bort mellanslaget före skiljetecknet'),
            (_SPACE_INSIDE_PARENS, 'Ta bort mellanslaget innanför parentesen'),
            (_ENGLISH_CURLY_QUOTES, 'Använd svenska citattecken ”…”'),
            (_LARGE_DOTTED_NUMBER, 'Gruppera stora tal med mellanslag, inte punkt'),
            (_PERCENT_WITHOUT_SPACE, 'Sätt mellanslag före procenttecknet'),
            (_SPACED_NUMERIC_HYPHEN, 'Använd tankstreck i talintervall'),
        ):
            for m in pattern.finditer(text):
                # Chapter 12.3 permits spacing before three dots when they
                # mark an omission or pause; do not treat that as a space
                # before an ordinary period.
                if (pattern is _SPACE_BEFORE_PUNCTUATION
                        and m.group(0).endswith('.')
                        and text[m.end():m.end() + 2] == '..'):
                    continue
                # In CLI help, a standalone question mark is often a literal
                # metavariable: “Använd ? för MIME-typer”. It is not prose
                # punctuation. Keep the exemption deliberately narrow.
                context = text[max(0, m.start() - 32):m.end() + 32]
                if (pattern is _SPACE_BEFORE_PUNCTUATION and m.group(0).endswith('?')
                        and (re.search(r'(?:Använd|Skriv|Ange) \? (?:som|för|i|med)\b', context, re.I)
                             or re.search(r'\(\?\) av \?', context))):
                    continue
                # Literal command patterns retain their ASCII ellipsis syntax.
                if pattern is _SPACE_BEFORE_PUNCTUATION and re.search(r"['`]set [^'`]*\.\.\.['`]", context):
                    continue
                # In CLI help, a list item may use a punctuation character as
                # a literal glob pattern, for example ``- ?``. It is syntax,
                # not a space before prose punctuation.
                line_start = text.rfind("\n", 0, m.start()) + 1
                line_end = text.find("\n", m.end())
                line = text[line_start:None if line_end < 0 else line_end]
                if pattern is _SPACE_BEFORE_PUNCTUATION and re.match(r"[ \t]*-[ \t]+\?(?:[ \t]|$)", line):
                    continue
                # IPv4 addresses use dotted octets by design, rather than
                # Swedish thousands separators.
                if pattern is _LARGE_DOTTED_NUMBER and _IPV4_ADDRESS.fullmatch(m.group(0)):
                    continue
                issues.append(SkrivregelIssue(
                    rule="interpunktion",
                    word=m.group(0),
                    suggestion=suggestion,
                    context=self._context(text, m.start(), m.end()),
                    position=m.start(),
                    line=self._line_number(text, m.start()),
                ))

        if self._check_interpunktion:
            for m in _DOUBLE_SPACE.finditer(text):
                # Multiline CLI help deliberately indents wrapped lines and
                # nested list items. Leading indentation is layout, not a
                # doubled space in Swedish prose.
                line_start = text.rfind("\n", 0, m.start()) + 1
                if not text[line_start:m.start()].strip():
                    continue
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
            "interpunktion": 6,  # spacing, quotes, numbers, ranges
        }
