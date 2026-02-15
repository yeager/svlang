# 🇸🇪 svlang

**Swedish NLP toolkit for translators.**

Detect anglicisms, check translation consistency, and split compound words — all from the command line or Python.

## Installation

```bash
pip install svlang

# With .po file support
pip install svlang[po]
```

## CLI Usage

### Svengelska detector

Find unnecessary anglicisms in Swedish text:

```bash
$ svlang svengelska -t "Vi behöver implementera en ny approach"
  ⚠️  «implementera» → genomföra, införa
  ⚠️  «approach» → tillvägagångssätt, metod

$ svlang svengelska -f my_translation.txt
```

### Consistency checker

Find identical source strings with different translations:

```bash
$ svlang consistency file1.po file2.po
⚠️  2 inkonsistens(er) hittade:

  Källa: «Save»
    → «Spara»  (file1.po:12)
    → «Lagra»  (file2.po:45)

# Also supports Qt .ts files
$ svlang consistency translations/*.ts
```

### Compound splitter

Split Swedish compound words into components:

```bash
$ svlang compound barnbok solstol nattljus
  barnbok → barn + bok
  solstol → sol + stol
  nattljus → natt + ljus
```

## Python API

```python
from svlang.checkers import SvengelskaChecker, ConsistencyChecker, CompoundSplitter

# Anglicisms
checker = SvengelskaChecker()
hits = checker.check("Ge mig lite feedback")
for h in hits:
    print(f"{h.word} → {h.suggestion}")

# Consistency
con = ConsistencyChecker()
con.add("Save", "Spara", "file1.po:12")
con.add("Save", "Lagra", "file2.po:45")
for issue in con.check():
    print(f"{issue.source}: {list(issue.translations.keys())}")

# Compound words
splitter = CompoundSplitter()
result = splitter.split("barnvagnshjul")
print(result.parts)  # ["barn", "vagn", "hjul"]
```

## Features

- 🔍 **90+ anglicisms** detected with Swedish alternatives (based on Språkrådet)
- 📊 **Consistency checking** across .po and .ts files
- 🧩 **Compound word splitting** with Swedish morphology (fogmorfem)
- 🖥️ **CLI** with colored output
- 📦 **Zero dependencies** (polib optional for .po files)
- 🐍 **Python 3.10+**

## Roadmap

- [ ] Spelling checker (Hunspell integration)
- [ ] Word frequency analysis
- [ ] Terminology extraction
- [ ] Gender-neutral language suggestions
- [ ] GitHub Action for CI validation
- [ ] LinguaEdit plugin

## 🌍 Contributing Translations

This app is translated via Transifex. Help translate it into your language!

**[→ Translate on Transifex](https://app.transifex.com/danielnylander/svlang/)**

Currently supported: Swedish (sv). More languages welcome!

### For Translators
1. Create a free account at [Transifex](https://www.transifex.com)
2. Join the [danielnylander](https://app.transifex.com/danielnylander/) organization
3. Start translating!

Translations are automatically synced via GitHub Actions.

## License

MIT

## Author

**Daniel Nylander** — [danielnylander.se](https://www.danielnylander.se)
