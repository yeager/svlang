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


def _cmd_skrivregler(args):
    """Check Swedish writing rules."""
    from svlang.checkers.skrivregler import SkrivreglerChecker
    checker = SkrivreglerChecker(
        check_sarskrivning=not args.disable_sarskrivning,
        check_dedem=not args.disable_dedem,
        check_stavfel=not args.disable_stavfel,
        check_interpunktion=getattr(args, 'enable_interpunktion', False),
    )

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

    issues = checker.check(text)

    if args.json:
        _output({
            "file": getattr(args, 'file', None),
            "issues": [
                {"rule": i.rule, "word": i.word, "suggestion": i.suggestion,
                 "line": i.line, "context": i.context}
                for i in issues
            ],
            "count": len(issues),
            "by_rule": {
                rule: len([i for i in issues if i.rule == rule])
                for rule in sorted(set(i.rule for i in issues))
            },
        }, as_json=True)
    elif not args.quiet:
        if not issues:
            source = Path(args.file).name if args.file else _("text")
            print(_("✅ {source}: Inga skrivregelfel hittades.").format(source=source))
        else:
            if args.file:
                print(_("⚠️  {name}: {count} skrivregelfel").format(
                    name=Path(args.file).name, count=len(issues)))
            by_rule: dict[str, list] = {}
            for i in issues:
                by_rule.setdefault(i.rule, []).append(i)
            for rule, items in sorted(by_rule.items()):
                rule_labels = {
                    "sarskrivning": "📝 Särskrivning",
                    "dedem": "🔤 De/dem",
                    "stavfel": "✏️ Stavfel",
                    "interpunktion": "⚙️ Interpunktion",
                }
                print(f"\n  {rule_labels.get(rule, rule)} ({len(items)}):")
                for i in items:
                    print(f"    rad {i.line}: «{i.word}» → {i.suggestion}")

    return 1 if issues else 0


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
            print(f"  {result.word} — {', '.join(r.translations)}")
        else:
            print(_("  «{word}» not found in dictionary").format(word=args.word))
    return 0 if result.found else 1


def _cmd_check(args):
    """Comprehensive text analysis."""
    from svlang.checkers.frequency import SwedishFrequency
    from svlang.checkers.naturalness import SwedishNaturalness
    from svlang.checkers.compound import CompoundSplitter
    from svlang.checkers.svengelska import SvengelskaChecker
    from svlang.checkers.skrivregler import SkrivreglerChecker

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

    # Run all checks
    freq_analyzer = SwedishFrequency()
    naturalness_analyzer = SwedishNaturalness()
    svengelska_checker = SvengelskaChecker()
    skrivregler_checker = SkrivreglerChecker()

    # Frequency analysis
    rare_words = freq_analyzer.analyze_text(text, threshold=args.frequency_threshold)
    
    # Naturalness analysis
    naturalness = naturalness_analyzer.analyze(text)
    
    # Anglicisms
    anglicisms = svengelska_checker.check(text)
    
    # Writing rules
    writing_issues = skrivregler_checker.check(text)

    if args.json:
        _output({
            "file": getattr(args, 'file', None),
            "naturalness_score": naturalness.score,
            "rare_words": [
                {"word": w.word, "score": w.frequency_score, "rank": w.rank}
                for w in rare_words
            ],
            "naturalness_issues": [
                {"category": i.category, "description": i.description, "severity": i.severity}
                for i in naturalness.issues
            ],
            "anglicisms": [{"word": a.word, "suggestion": a.suggestion} for a in anglicisms],
            "writing_issues": [
                {"rule": i.rule, "word": i.word, "suggestion": i.suggestion, "line": i.line}
                for i in writing_issues
            ],
            "statistics": {
                "sentence_count": naturalness.sentence_count,
                "avg_sentence_length": naturalness.avg_sentence_length,
                "passive_ratio": naturalness.passive_ratio,
                "rare_word_count": len(rare_words),
                "anglicism_count": len(anglicisms),
                "writing_issue_count": len(writing_issues)
            }
        }, as_json=True)
    elif not args.quiet:
        source = Path(args.file).name if args.file else "text"
        print(f"📊 Analyserar {source}...")
        print()
        
        # Naturalness score
        print(f"🎯 Naturlighetspoäng: {naturalness.score:.1f}/10")
        if naturalness.score < 7:
            print("   ⚠️ Låg poäng kan tyda på maskinöversättning eller onaturlig svenska")
        print()
        
        # Statistics
        print(f"📈 Statistik:")
        print(f"   Meningar: {naturalness.sentence_count}")
        print(f"   Genomsnittlig meningslängd: {naturalness.avg_sentence_length:.1f} ord")
        if naturalness.avg_sentence_length > 25:
            print("   ⚠️ Långa meningar kan påverka läsbarheten")
        print()
        
        # Rare words
        if rare_words:
            print(f"🔍 Ovanliga ord ({len(rare_words)}):")
            for word in rare_words[:10]:  # Show top 10
                level = freq_analyzer.get_word_rarity_level(word.frequency_score)
                rank_str = f" (#{word.rank})" if word.rank else " (okänt)"
                print(f"   «{word.word}»{rank_str} — {level}")
            if len(rare_words) > 10:
                print(f"   ... och {len(rare_words) - 10} till")
            print()
        
        # Naturalness issues
        if naturalness.issues:
            print(f"⚠️ Naturlighetsproblem ({len(naturalness.issues)}):")
            for issue in naturalness.issues:
                print(f"   {issue.category}: {issue.description}")
                if issue.context:
                    print(f"     Kontext: {issue.context}")
            print()
        
        # Anglicisms  
        if anglicisms:
            print(f"🇬🇧 Anglicismer ({len(anglicisms)}):")
            for a in anglicisms:
                print(f"   «{a.word}» → {a.suggestion}")
            print()
        
        # Writing issues
        if writing_issues:
            print(f"✏️ Skrivregelfel ({len(writing_issues)}):")
            by_rule = {}
            for i in writing_issues:
                by_rule.setdefault(i.rule, []).append(i)
            for rule, items in sorted(by_rule.items()):
                print(f"   {rule}: {len(items)} fel")
                for i in items[:3]:  # Show first 3 per rule
                    print(f"     rad {i.line}: «{i.word}» → {i.suggestion}")
                if len(items) > 3:
                    print(f"     ... och {len(items) - 3} till")
            print()

        # Summary
        total_issues = len(rare_words) + len(naturalness.issues) + len(anglicisms) + len(writing_issues)
        if total_issues == 0:
            print("✅ Inga problem hittades!")
        else:
            print(f"📋 Sammanfattning: {total_issues} problem hittade")

    # Return non-zero if significant issues found
    major_issues = len([i for i in naturalness.issues if i.severity > 0.5]) + len(anglicisms) + len(writing_issues)
    return 1 if major_issues > 0 else 0


def _cmd_freq(args):
    """Word frequency lookup."""
    from svlang.checkers.frequency import SwedishFrequency
    
    freq = SwedishFrequency()
    result = freq.get_frequency_score(args.word)
    
    if args.json:
        _output({
            "word": result.word,
            "found": result.found,
            "frequency_score": result.frequency_score,
            "rank": result.rank,
            "level": freq.get_word_rarity_level(result.frequency_score)
        }, as_json=True)
    elif not args.quiet:
        level = freq.get_word_rarity_level(result.frequency_score)
        if result.found:
            print(f"📊 «{result.word}»")
            print(f"   Rang: #{result.rank} av {freq.total_words}")
            print(f"   Frekvenspoäng: {result.frequency_score:.3f}")
            print(f"   Nivå: {level}")
        else:
            print(f"📊 «{result.word}»")
            print(f"   Status: Okänt ord")
            print(f"   Nivå: {level}")
    
    return 0


def _cmd_natural(args):
    """Naturalness analysis."""
    from svlang.checkers.naturalness import SwedishNaturalness
    
    if args.text:
        text = " ".join(args.text)
    else:
        if args.json:
            _output({"error": _("Specify --text")}, as_json=True)
        else:
            print(_("Specify --text"), file=sys.stderr)
        return 2

    analyzer = SwedishNaturalness()
    result = analyzer.analyze(text)
    
    if args.json:
        _output({
            "text": text,
            "score": result.score,
            "sentence_count": result.sentence_count,
            "avg_sentence_length": result.avg_sentence_length,
            "passive_ratio": result.passive_ratio,
            "anglicism_count": result.anglicism_count,
            "issues": [
                {"category": i.category, "description": i.description, "severity": i.severity, "context": i.context}
                for i in result.issues
            ]
        }, as_json=True)
    elif not args.quiet:
        print(f"🎯 Naturlighetspoäng: {result.score:.1f}/10")
        
        # Interpretation
        if result.score >= 8.5:
            print("   ✅ Mycket naturlig svenska")
        elif result.score >= 7.0:
            print("   ✓ Naturlig svenska")
        elif result.score >= 5.0:
            print("   ⚠️ Något onaturlig svenska")
        else:
            print("   ❌ Onaturlig svenska - misstänkt maskinöversättning")
        
        print()
        print(f"📊 Statistik:")
        print(f"   Meningar: {result.sentence_count}")
        print(f"   Genomsnittlig meningslängd: {result.avg_sentence_length:.1f} ord")
        print(f"   Passiv ratio: {result.passive_ratio:.1%}")
        print(f"   Anglicismer: {result.anglicism_count}")
        
        if result.issues:
            print()
            print(f"⚠️ Problem ({len(result.issues)}):")
            for issue in result.issues:
                severity_icon = "🚨" if issue.severity > 0.7 else "⚠️" if issue.severity > 0.3 else "ℹ️"
                print(f"   {severity_icon} {issue.description}")
                if issue.context:
                    print(f"     Kontext: {issue.context}")
    
    return 0


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

    # skrivregler
    p_skriv = sub.add_parser("skrivregler", aliases=["regler", "sr"], help=_("Check Swedish writing rules"))
    p_skriv.add_argument("--text", "-t", nargs="+", help=_("Text to check"))
    p_skriv.add_argument("--file", "-f", help=_("File to check"))
    p_skriv.add_argument("--disable-sarskrivning", action="store_true", help=_("Disable compound split check"))
    p_skriv.add_argument("--disable-dedem", action="store_true", help=_("Disable de/dem check"))
    p_skriv.add_argument("--disable-stavfel", action="store_true", help=_("Disable misspelling check"))
    p_skriv.add_argument("--enable-interpunktion", action="store_true", help=_("Enable punctuation check (off by default)"))
    p_skriv.add_argument("--disable-interpunktion", action="store_true", help=argparse.SUPPRESS)  # back-compat
    p_skriv.set_defaults(func=_cmd_skrivregler)

    # lookup
    p_look = sub.add_parser("lookup", aliases=["ord"], help=_("Look up sv→en (Folkets lexikon)"))
    p_look.add_argument("word", help=_("Word to look up"))
    p_look.add_argument("--reverse", "-r", action="store_true", help=_("Search en→sv"))
    p_look.add_argument("--search", "-s", action="store_true", help=_("Search prefix"))
    p_look.add_argument("--limit", "-n", type=int, default=20, help=_("Max results"))
    p_look.set_defaults(func=_cmd_lookup)

    # check (comprehensive analysis)
    p_check = sub.add_parser("check", help=_("Comprehensive text analysis"))
    p_check.add_argument("--text", "-t", nargs="+", help=_("Text to analyze"))
    p_check.add_argument("--file", "-f", help=_("File to analyze"))
    p_check.add_argument("--frequency-threshold", type=float, default=0.7, help=_("Threshold for flagging rare words (0.0-1.0)"))
    p_check.set_defaults(func=_cmd_check)

    # freq (frequency analysis)
    p_freq = sub.add_parser("freq", help=_("Word frequency lookup"))
    p_freq.add_argument("word", help=_("Word to analyze"))
    p_freq.set_defaults(func=_cmd_freq)

    # natural (naturalness analysis)
    p_natural = sub.add_parser("natural", help=_("Text naturalness analysis"))
    p_natural.add_argument("--text", "-t", nargs="+", help=_("Text to analyze"))
    p_natural.set_defaults(func=_cmd_natural)

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
