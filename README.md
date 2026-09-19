# svlang

![Version](https://img.shields.io/badge/version-0.2.1-blue)
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

Den senaste DEB-filen kan installeras direkt medan den signerade APT-katalogen
uppdateras:

```bash
curl -LO https://yeager.github.io/debian-repo/pool/main/s/svlang/svlang_0.2.0-2_all.deb
sudo apt install ./svlang_0.2.0-2_all.deb
```

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

- **Unreleased**: Accept both `iväg` and `i väg` in writing-rule checks, following Svensk ordbok.
- **0.2.1**: Document Computer Swedens IT-ord as the first terminology source for IT terms
- **0.2.0**: Latest stable release with enhanced Swedish language support
- **0.1.x**: Initial development and core NLP functionality

## License

MIT

## Author

Daniel Nylander (daniel@danielnylander.se)
