"""svlang CLI — Swedish NLP toolkit for translators."""

from __future__ import annotations

import argparse
import gettext
import json
import locale
import sys
from pathlib import Path

from svlang import __version__

TEXTDOMAIN = "svlang"
LOCALEDIR = "/usr/share/locale"
try:
    locale.bindtextdomain(TEXTDOMAIN, LOCALEDIR)
    locale.textdomain(TEXTDOMAIN)
except AttributeError:
    pass
_ = gettext.gettext


def _output(data, as_json=False, quiet=False):
    """Output data as JSON or human-readable text."""
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif not quiet:
        if isinstance(data, str):
            print(data)
        elif isinstance(data, list):
            for line in data:
                print(line)


def _cmd_svengelska(args):
    """Check for anglicisms."""
    from svlang.checkers.svengelska import SvengelskaChecker
    checker = SvengelskaChecker()

    if args.text:
        text = " ".join(args.text)
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            if args.json:
                _output({"error": _("File not found: {path}").format(path=path)}, as_json=True)
            else:
                print(_("File not found: {path}").format(path=path), file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8")
    else:
        if args.json:
            _output({"error": _("Specify --text or --file")}, as_json=True)
        else:
            print(_("Specify --text or --file"), file=sys.stderr)
        return 2

    hits = checker.check(text)
    if args.json:
        _output({
            "file": getattr(args, 'file', None),
            "hits": [{"word": h.word, "suggestion": h.suggestion, "context": getattr(h, 'context', '')} for h in hits],
            "count": len(hits),
        }, as_json=True)
    elif not args.quiet:
        if not hits:
            source = Path(args.file).name if args.file else _("text")
            print(_("✅ {source}: No anglicisms found.").format(source=source))
        else:
            if args.file:
                print(_("⚠️  {name}: {count} anglicism(s)").format(name=Path(args.file).name, count=len(hits)))
            for h in hits:
                print(_("  ⚠️  «{word}» → {suggestion}").format(word=h.word, suggestion=h.suggestion))
                if hasattr(h, 'context') and h.context:
                    print(f"    ...{h.context}...")

    return 1 if hits else 0


def _cmd_consistency(args):
    """Check translation consistency."""
    from svlang.checkers.consistency import ConsistencyChecker
    checker = ConsistencyChecker(case_sensitive=not args.ignore_case)

    for path in args.files:
        p = Path(path)
        if not p.exists():
            print(_("File not found: {path}").format(path=p), file=sys.stderr)
            continue
        if p.suffix == ".po":
            checker.add_po_file(str(p))
        elif p.suffix == ".ts":
            checker.add_ts_file(str(p))
        else:
            print(_("Unsupported format: {suffix} (use .po or .ts)").format(suffix=p.suffix), file=sys.stderr)

    issues = checker.check()

    if args.json:
        _output({
            "issues": [{"source": i.source, "translations": i.translations} for i in issues],
            "count": len(issues),
        }, as_json=True)
    elif not args.quiet:
        if not issues:
            print(_("✅ All translations are consistent."))
        else:
            print(_("⚠️  {count} inconsistency(ies) found:").format(count=len(issues)))
            print()
            for issue in issues:
                print(_("  Source: «{source}»").format(source=issue.source))
                for trans, locs in issue.translations.items():
                    loc_str = ", ".join(locs[:3])
                    if len(locs) > 3:
                        loc_str += f" (+{len(locs) - 3})"
                    print(f"    → «{trans}»  ({loc_str})")
                print()

    return 1 if issues else 0


def _cmd_compound(args):
    """Split compound words."""
    from svlang.checkers.compound import CompoundSplitter
    splitter = CompoundSplitter()

    results = []
    for word in args.words:
        result = splitter.split(word)
        results.append({
            "word": word,
            "is_compound": result.is_compound,
            "parts": result.parts if result.is_compound else [],
        })

    if args.json:
        _output({"results": results}, as_json=True)
    elif not args.quiet:
        for r in results:
            if r["is_compound"]:
                print(f"  {r['word']} → {' + '.join(r['parts'])}")
            else:
                print(_("  {word} → (not a compound)").format(word=r['word']))
    return 0


def _cmd_lix(args):
    """Calculate LIX readability index."""
    from svlang.checkers.readability import LixCalculator
    calc = LixCalculator()

    if args.text:
        text = " ".join(args.text)
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            if args.json:
                _output({"error": _("File not found: {path}").format(path=path)}, as_json=True)
            else:
                print(_("File not found: {path}").format(path=path), file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8")
    else:
        if args.json:
            _output({"error": _("Specify --text or --file")}, as_json=True)
        else:
            print(_("Specify --text or --file"), file=sys.stderr)
        return 2

    result = calc.calculate(text)
    if args.json:
        _output({
            "lix": result.score,
            "level": result.level,
            "words": result.words,
            "sentences": result.sentences,
            "long_words": result.long_words,
        }, as_json=True)
    elif not args.quiet:
        print(_("  LIX: {score}").format(score=result.score))
        print(_("  Level: {level}").format(level=result.level))
        print(_("  Words: {count}").format(count=result.words))
        print(_("  Sentences: {count}").format(count=result.sentences))
        print(_("  Long words (>6 chars): {count}").format(count=result.long_words))
    return 0


def _cmd_lookup(args):
    """Dictionary lookup."""
    from svlang.checkers.lexicon import SwedishLexicon
    lex = SwedishLexicon()

    if args.reverse:
        results = lex.reverse_lookup(args.word, limit=args.limit)
        if args.json:
            _output({
                "query": args.word,
                "direction": "en→sv",
                "results": [{"word": r.word, "translations": r.translations} for r in results],
            }, as_json=True)
        elif not args.quiet:
            if not results:
                print(_("No Swedish words found for «{word}»").format(word=args.word))
            else:
                print(_("🔍 English «{word}» → Swedish:").format(word=args.word))
                for r in results:
                    print(f"  {r.word} — {', '.join(r.translations)}")
        return 0 if results else 1

    if args.search:
        results = lex.search(args.word, limit=args.limit)
        if args.json:
            _output({
                "query": args.word,
                "type": "prefix",
                "results": [{"word": r.word, "translations": r.translations} for r in results],
            }, as_json=True)
        elif not args.quiet:
            if not results:
                print(_("No words starting with «{word}»").format(word=args.word))
            else:
                for r in results:
                    print(f"  {r.word} — {', '.join(r.translations)}")
        return 0 if results else 1

    result = lex.lookup(args.word)
    if args.json:
        _output({
            "query": args.word,
            "found": result.found,
            "word": result.word if result.found else None,
            "translations": result.translations if result.found else [],
        }, as_json=True)
    elif not args.quiet:
        if result.found:
            print(f"  {result.word} — {', '.join(result.translations)}")
        else:
            print(_("  «{word}» not found in dictionary").format(word=args.word))
    return 0 if result.found else 1


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="svlang",
        description=_("🇸🇪 Swedish NLP toolkit for translators"),
    )
    parser.add_argument("-V", "--version", action="version", version=f"svlang {__version__}")
    parser.add_argument("--about", action="store_true", help=_("Show application info and exit"))
    parser.add_argument("--json", "-j", action="store_true", help=_("JSON output"))
    parser.add_argument("--quiet", "-q", action="store_true", help=_("Suppress non-essential output"))
    sub = parser.add_subparsers(dest="command", help=_("Command"))

    # svengelska
    p_sv = sub.add_parser("svengelska", aliases=["sv"], help=_("Find anglicisms"))
    p_sv.add_argument("--text", "-t", nargs="+", help=_("Text to check"))
    p_sv.add_argument("--file", "-f", help=_("File to check"))
    p_sv.set_defaults(func=_cmd_svengelska)

    # consistency
    p_con = sub.add_parser("consistency", aliases=["con"], help=_("Check consistency"))
    p_con.add_argument("files", nargs="+", help=_(".po or .ts files"))
    p_con.add_argument("--ignore-case", "-i", action="store_true")
    p_con.set_defaults(func=_cmd_consistency)

    # compound
    p_comp = sub.add_parser("compound", aliases=["split"], help=_("Split compound words"))
    p_comp.add_argument("words", nargs="+", help=_("Words to split"))
    p_comp.set_defaults(func=_cmd_compound)

    # lix
    p_lix = sub.add_parser("lix", help=_("Calculate LIX readability index"))
    p_lix.add_argument("--text", "-t", nargs="+", help=_("Text to analyze"))
    p_lix.add_argument("--file", "-f", help=_("File to analyze"))
    p_lix.set_defaults(func=_cmd_lix)

    # lookup
    p_look = sub.add_parser("lookup", aliases=["ord"], help=_("Look up sv→en (Folkets lexikon)"))
    p_look.add_argument("word", help=_("Word to look up"))
    p_look.add_argument("--reverse", "-r", action="store_true", help=_("Search en→sv"))
    p_look.add_argument("--search", "-s", action="store_true", help=_("Search prefix"))
    p_look.add_argument("--limit", "-n", type=int, default=20, help=_("Max results"))
    p_look.set_defaults(func=_cmd_lookup)

    args = parser.parse_args(argv)
    if args.about:
        print(f"svlang {__version__}")
        print(_("Swedish NLP toolkit for translators"))
        print()
        print(f"{_('Author')}:     Daniel Nylander <daniel@danielnylander.se>")
        print(f"{_('License')}:    GPL-3.0-or-later")
        print(f"{_('Website')}:    https://github.com/yeager/svlang")
        print(f"{_('PyPI')}:       https://pypi.org/project/svlang/")
        print(f"{_('Translate')}:  https://app.transifex.com/danielnylander/svlang/")
        return 0
    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
