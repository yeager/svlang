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

### Debian/Ubuntu

DEB-filen för version 0.2.7 finns i [GitHub-releasen](https://github.com/yeager/svlang/releases/tag/v0.2.7):

```bash
curl -LO https://github.com/yeager/svlang/releases/download/v0.2.7/svlang_0.2.7-1_all.deb
sudo apt install ./svlang_0.2.7-1_all.deb
```

Releasen innehåller även en Python-wheel, ett källarkiv och `SHA256SUMS`.
APT/RPM-kataloger och PyPI kan fortfarande innehålla en äldre version.

### pip
```bash
pip install svlang
```

## Building from source

```bash
git clone https://github.com/yeager/svlang
cd svlang
pip install -e .
```

## Usage

Check Swedish text:
```bash
svlang check --file text.txt
```

Check Swedish writing rules:
```bash
svlang skrivregler --file file.txt

# Visa hela stilpolicyn och manuella granskningspunkter
svlang skrivregler --style-guide
```

Check text naturalness (heuristics, not a complete grammar checker):
```bash
svlang natural --text "Det här är en svensk mening."
```

Show help and all options:
```bash
svlang --help
man svlang
```

## Frekvens och stavningskontroll

`check` consults both bundled Swedish lexicons before flagging a word missing
from the estimated frequency list. If `hunspell` and its `sv_SE` dictionary are
installed, inflected forms are checked there too. Without them, the bundled
lexicons still work, but morphological coverage is narrower.

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

## Terminology sources

For IT terminology, svlang's project guidance uses [Computer Swedens
IT-ord](https://it-ord.computersweden.se/) as the first reference source. For
other terminology and general Swedish it uses [SAOL, SO and
SAOB](https://svenska.se/), [TEPA](https://termipankki.fi/tepa/sv/),
[IATE](https://iate.europa.eu/home), [Rikstermbanken](https://www.rikstermbanken.se/)
and [ISOF's guidance on fackspråk och terminologi](https://www.isof.se/svenska-spraket/facksprak-och-terminologi).
They are consulted as reference sources; svlang does not scrape or redistribute
their content.

## Development

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

Tests simulate Hunspell availability and failure; system dictionaries are not
required to run the suite.

## Translation

Translations are managed on Transifex: https://app.transifex.com/danielnylander/svlang/

Currently supported: Swedish, Danish, German, Spanish, Finnish, French, Italian, Norwegian Bokmål, Dutch, Polish, Portuguese (Brazil)

Contributions welcome!

## Changelog

- **0.2.7**: Add the documented Swedish style-policy checklist and typography checks.
- **0.2.6**: Flag punctuation-spacing errors and ASCII three-dot ellipses.
- **0.2.5**: Flag commas immediately before `och` in Swedish translations.

- **0.2.2**: Accept both `iväg` and `i väg` in writing-rule checks, following Svensk ordbok.
- **0.2.1**: Document Computer Swedens IT-ord as the first terminology source for IT terms
- **0.2.0**: Latest stable release with enhanced Swedish language support
- **0.1.x**: Initial development and core NLP functionality

## License

MIT

## Author

Daniel Nylander (daniel@danielnylander.se)
