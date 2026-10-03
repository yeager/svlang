# svlang

[![Version](https://img.shields.io/badge/version-0.2.7-blue)](https://github.com/yeager/svlang/releases/tag/v0.2.7)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)

## Beskrivning

svlang är ett kommandoradsverktyg för svensk språkgranskning i
översättningsflöden. Det erbjuder ordkontroll, frekvensuppslag, skrivregler och
heuristisk kontroll av hur naturlig en mening verkar. Verktyget ger snabb
återkoppling, men ersätter inte språkgranskning i sitt sammanhang.

## Funktioner

- `check` kontrollerar ord mot de medföljande svenska lexikonen och, när det
  finns, Hunspells svenska ordlista.
- `freq` visar förekomst i den uppskattade frekvenslistan.
- `skrivregler` hittar vanliga formella skrivregelavvikelser.
- `natural` ger heuristiska signaler om formuleringar som kan behöva ses över.

## Installation

### Fedora/RHEL
```bash
sudo dnf config-manager addrepo --from-repofile=https://yeager.github.io/rpm-repo/yeager.repo
sudo dnf makecache
sudo dnf install svlang
```

### Aktuell version

[Version 0.2.7](https://github.com/yeager/svlang/releases/tag/v0.2.7) innehåller
versionsanteckningar och den annoterade Git-taggen. Installera via `pip` eller
från källkod enligt anvisningarna nedan. APT- och RPM-kataloger kan ligga efter
den senaste GitHub-versionen.

### pip
```bash
pip install svlang
```

## Bygg från källkod

```bash
git clone https://github.com/yeager/svlang
cd svlang
pip install -e .
```

## Användning

Kontrollera svensk text:
```bash
svlang check --file text.txt
```

Kontrollera svenska skrivregler:
```bash
svlang skrivregler --file file.txt

# Visa hela stilpolicyn och manuella granskningspunkter
svlang skrivregler --style-guide
```

Kontrollera språklig naturlighet (heuristik, inte en fullständig grammatikkontroll):
```bash
svlang natural --text "Det här är en svensk mening."
```

Visa hjälp och alla alternativ:
```bash
svlang --help
man svlang
```

## Frekvens och stavningskontroll

`check` kontrollerar båda de medföljande svenska lexikonen innan ett ord som
saknas i frekvenslistan markeras. Om `hunspell` och dess `sv_SE`-ordlista är
installerade kontrolleras även böjda former där. Utan dem fungerar de
medföljande lexikonen fortfarande, men den morfologiska täckningen är mindre.

Frekvenslistan är en uppskattning byggd av vanliga ord och en ordlista, inte
uppmätta korpusfrekvenser. `freq` visar bara förekomst i den listan;
`found: false` betyder inte att ordet är felstavat. Frekvensförslag är råd och
gör inte ensamma att `check` avslutas med status 1.

## Gemensam språkgranskning

Använd `svlang` tillsammans med [l10n-lint](https://github.com/yeager/l10n-lint),
[hunspell-sv](https://github.com/yeager/hunspell-sv),
[swedish-foss-terminology](https://github.com/yeager/swedish-foss-terminology) och
[swedish-tm](https://github.com/yeager/swedish-tm). Kör först katalog- och
platshållarkontroller, sedan stavning och skrivregler. Kontrollera därefter
varje varning mot källtext, gränssnittskontext och projektets terminologi.

`skrivregler` kontrollerar mekaniskt sådant som kan avgöras utan sammanhang:
komma omedelbart före `och` enligt projektets policy, mellanslag före svensk
skiljeteckning, svenska citattecken, utelämningstecknet `…`, mellanrum före
procenttecken, tusentalsgruppering och tankstreck i talintervall.
[Stilpolicyn](docs/swedish-style-guide.md) beskriver kontrollerna och de
regler som alltid måste granskas manuellt, exempelvis tilltal, betydelse,
register och tvetydiga termer. En text före `|` i en Crowdin-nyckel är
kontextmetadata och får inte läcka in i den synliga svenska översättningen.

## Terminologikällor

För IT-terminologi använder svlangs projektriktlinjer [Computer Swedens
IT-ord](https://it-ord.computersweden.se/) som första referenskälla. För annan
terminologi och allmän svenska används [SAOL, SO och
SAOB](https://svenska.se/), [TEPA](https://termipankki.fi/tepa/sv/),
[IATE](https://iate.europa.eu/home), [Rikstermbanken](https://www.rikstermbanken.se/)
och [ISOF:s vägledning om fackspråk och terminologi](https://www.isof.se/svenska-spraket/facksprak-och-terminologi).
De används som referenskällor. svlang samlar inte in eller återdistribuerar deras innehåll.

## Utveckling

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

Tester simulerar tillgänglig och otillgänglig Hunspell. Systemordlistor krävs inte för att köra sviten.

## Översättning

Översättningar hanteras på Transifex: https://app.transifex.com/danielnylander/svlang/

Språk som stöds: svenska, danska, tyska, spanska, finska, franska, italienska, norskt bokmål, nederländska, polska och portugisiska (Brasilien)

Bidrag välkomnas!

## Changelog

- **0.2.7**: Lägger till den dokumenterade svenska stilpolicyn och typografikontroller.
- **0.2.6**: Markerar felaktiga mellanslag vid skiljetecken och tre ASCII-punkter.
- **0.2.5**: Markerar kommatecken omedelbart före `och` i svenska översättningar.
- **0.2.2**: Accepterar både `iväg` och `i väg` i skrivregelkontroller enligt Svensk ordbok.
- **0.2.1**: Dokumenterar Computer Swedens IT-ord som första terminologikälla för IT-termer.
- **0.2.0**: Stabil version med utökat stöd för svenska.
- **0.1.x**: Första utveckling och grundläggande NLP-funktioner.

## Licens

MIT

## Upphovsperson

Daniel Nylander (daniel@danielnylander.se)

## English reference

svlang is a command-line helper for Swedish localization review. Use `check` for
word-list and Hunspell-backed spelling signals, `freq` for frequency lookups,
`skrivregler` for mechanical style checks, and `natural` for heuristic wording
signals. Run `svlang skrivregler --style-guide` for the complete policy.

Use it with l10n-lint, hunspell-sv, swedish-foss-terminology and swedish-tm.
Automatic checks cover the project rule against a comma directly before `och`,
punctuation spacing, Swedish quotation marks, ellipses, percentages, digit
grouping and numeric ranges. Meaning, tone, register and context-specific
terminology remain manual review tasks. A Crowdin prefix before `|` is metadata
and must not appear in the visible Swedish translation.
