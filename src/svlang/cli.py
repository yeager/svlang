"""svlang CLI — Swedish NLP toolkit for translators."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from svlang import __version__


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
                _output({"error": f"Filen finns inte: {path}"}, as_json=True)
            else:
                print(f"Filen finns inte: {path}", file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8")
    else:
        if args.json:
            _output({"error": "Ange --text eller --file"}, as_json=True)
        else:
            print("Ange --text eller --file", file=sys.stderr)
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
            source = Path(args.file).name if args.file else "text"
            print(f"✅ {source}: Inga anglicismer hittade.")
        else:
            if args.file:
                print(f"⚠️  {Path(args.file).name}: {len(hits)} anglicism(er)")
            for h in hits:
                print(f"  ⚠️  «{h.word}» → {h.suggestion}")
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
            print(f"Filen finns inte: {p}", file=sys.stderr)
            continue
        if p.suffix == ".po":
            checker.add_po_file(str(p))
        elif p.suffix == ".ts":
            checker.add_ts_file(str(p))
        else:
            print(f"Format stöds inte: {p.suffix} (använd .po eller .ts)", file=sys.stderr)

    issues = checker.check()

    if args.json:
        _output({
            "issues": [{"source": i.source, "translations": i.translations} for i in issues],
            "count": len(issues),
        }, as_json=True)
    elif not args.quiet:
        if not issues:
            print("✅ Alla översättningar är konsekventa.")
        else:
            print(f"⚠️  {len(issues)} inkonsistens(er) hittade:\n")
            for issue in issues:
                print(f"  Källa: «{issue.source}»")
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
                print(f"  {r['word']} → (ej sammansatt)")
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
                _output({"error": f"Filen finns inte: {path}"}, as_json=True)
            else:
                print(f"Filen finns inte: {path}", file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8")
    else:
        if args.json:
            _output({"error": "Ange --text eller --file"}, as_json=True)
        else:
            print("Ange --text eller --file", file=sys.stderr)
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
        print(f"  LIX: {result.score}")
        print(f"  Nivå: {result.level}")
        print(f"  Ord: {result.words}")
        print(f"  Meningar: {result.sentences}")
        print(f"  Långa ord (>6 tecken): {result.long_words}")
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
                print(f"Inga svenska ord hittades för «{args.word}»")
            else:
                print(f"🔍 Engelska «{args.word}» → svenska:")
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
                print(f"Inga ord börjar med «{args.word}»")
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
            print(f"  «{args.word}» finns inte i ordboken")
    return 0 if result.found else 1


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="svlang",
        description="🇸🇪 Svenskt NLP-verktyg för översättare",
    )
    parser.add_argument("-V", "--version", action="version", version=f"svlang {__version__}")
    parser.add_argument("--about", action="store_true", help="Visa programinfo och avsluta")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress non-essential output")
    sub = parser.add_subparsers(dest="command", help="Kommando")

    # svengelska
    p_sv = sub.add_parser("svengelska", aliases=["sv"], help="Hitta anglicismer")
    p_sv.add_argument("--text", "-t", nargs="+", help="Text att kontrollera")
    p_sv.add_argument("--file", "-f", help="Fil att kontrollera")
    p_sv.set_defaults(func=_cmd_svengelska)

    # consistency
    p_con = sub.add_parser("consistency", aliases=["con"], help="Kontrollera konsekvens")
    p_con.add_argument("files", nargs="+", help=".po- eller .ts-filer")
    p_con.add_argument("--ignore-case", "-i", action="store_true")
    p_con.set_defaults(func=_cmd_consistency)

    # compound
    p_comp = sub.add_parser("compound", aliases=["split"], help="Dela upp sammansatta ord")
    p_comp.add_argument("words", nargs="+", help="Ord att dela")
    p_comp.set_defaults(func=_cmd_compound)

    # lix
    p_lix = sub.add_parser("lix", help="Beräkna LIX läsbarhetsindex")
    p_lix.add_argument("--text", "-t", nargs="+", help="Text att analysera")
    p_lix.add_argument("--file", "-f", help="Fil att analysera")
    p_lix.set_defaults(func=_cmd_lix)

    # lookup
    p_look = sub.add_parser("lookup", aliases=["ord"], help="Slå upp sv→en (Folkets lexikon)")
    p_look.add_argument("word", help="Ord att slå upp")
    p_look.add_argument("--reverse", "-r", action="store_true", help="Sök en→sv")
    p_look.add_argument("--search", "-s", action="store_true", help="Sök prefix")
    p_look.add_argument("--limit", "-n", type=int, default=20, help="Max resultat")
    p_look.set_defaults(func=_cmd_lookup)

    args = parser.parse_args(argv)
    if args.about:
        print(f"svlang {__version__}")
        print("Swedish NLP toolkit for translators")
        print()
        print("Author:     Daniel Nylander <daniel@danielnylander.se>")
        print("License:    GPL-3.0-or-later")
        print("Website:    https://github.com/yeager/svlang")
        print("PyPI:       https://pypi.org/project/svlang/")
        print("Translate:  https://app.transifex.com/danielnylander/svlang/")
        return 0
    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
