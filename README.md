# svlang

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)

## Description

Swedish NLP toolkit designed specifically for translators and localization professionals. svlang provides essential language tools including spell checking, grammar validation, and declension support for Swedish text processing and quality assurance.

This command-line tool is part of the professional L10n Tool Suite, offering specialized Swedish language support that traditional tools often lack, making it invaluable for translators working with Swedish content.

## Features

- **Swedish spell checking**: Advanced spell checking tailored for Swedish
- **Grammar validation**: Swedish grammar and syntax analysis
- **Declension support**: Proper Swedish word inflection handling
- **Translation-focused**: Designed specifically for localization workflows
- **CLI interface**: Efficient command-line tool for automation
- **Swedish expertise**: Built by Swedish translators for Swedish translation
- **Lightweight**: Minimal dependencies, fast processing
- **Extensible**: Modular design for additional Swedish NLP features

## Installation

### APT (Debian/Ubuntu)
```bash
echo "deb https://yeager.github.io/debian-repo stable main" | sudo tee /etc/apt/sources.list.d/yeager-l10n.list
curl -fsSL https://yeager.github.io/debian-repo/yeager-l10n.gpg | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/yeager-l10n.gpg
sudo apt update && sudo apt install svlang
```

### DNF (Fedora)
```bash
sudo dnf config-manager --add-repo https://yeager.github.io/rpm-repo/yeager-l10n.repo
sudo dnf install svlang
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

## Frequency and spelling coverage

`check` consults both bundled Swedish lexicons before flagging a word missing
from the estimated frequency list. If `hunspell` and its `sv_SE` dictionary are
installed, inflected forms are checked there too. Without them, the bundled
lexicons still work, but morphological coverage is narrower.

The frequency list is an estimate assembled from common words and a wordlist,
not measured corpus frequencies. `freq` reports presence in that list;
`found: false` does **not** mean a word is misspelled. Frequency suggestions are
advisory and do not alone make `check` exit with status 1.

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

- **0.2.0**: Latest stable release with enhanced Swedish language support
- **0.1.x**: Initial development and core NLP functionality

## License

MIT

## Author

Daniel Nylander (daniel@danielnylander.se)
