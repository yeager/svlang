"""svlang CLI — Swedish NLP toolkit for translators."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from svlang import __version__


def _cmd_svengelska(args):
    """Check for anglicisms."""
    from svlang.checkers.svengelska import SvengelskaChecker
    checker = SvengelskaChecker()

    if args.text:
        text = " ".join(args.text)
        hits = checker.check(text)
        if not hits:
            print("✅ Inga anglicismer hittade.")
            return 0
        for h in hits:
            print(f"  ⚠️  «{h.word}» → {h.suggestion}")
        return 1 if hits else 0

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Filen finns inte: {path}", file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8")
        hits = checker.check(text)
        if not hits:
            print(f"✅ {path.name}: Inga anglicismer hittade.")
            return 0
        print(f"⚠️  {path.name}: {len(hits)} anglicism(er)")
        for h in hits:
            print(f"  «{h.word}» → {h.suggestion}")
            print(f"    ...{h.context}...")
        return 1

    print("Ange --text eller --file", file=sys.stderr)
    return 2


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
    if not issues:
        print("✅ Alla översättningar är konsekventa.")
        return 0

    print(f"⚠️  {len(issues)} inkonsistens(er) hittade:\n")
    for issue in issues:
        print(f"  Källa: «{issue.source}»")
        for trans, locs in issue.translations.items():
            loc_str = ", ".join(locs[:3])
            if len(locs) > 3:
                loc_str += f" (+{len(locs) - 3})"
            print(f"    → «{trans}»  ({loc_str})")
        print()
    return 1


def _cmd_compound(args):
    """Split compound words."""
    from svlang.checkers.compound import CompoundSplitter
    splitter = CompoundSplitter()

    for word in args.words:
        result = splitter.split(word)
        if result.is_compound:
            print(f"  {word} → {' + '.join(result.parts)}")
        else:
            print(f"  {word} → (ej sammansatt)")
    return 0


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="svlang",
        description="🇸🇪 Svenskt NLP-verktyg för översättare",
    )
    parser.add_argument("-V", "--version", action="version", version=f"svlang {__version__}")
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

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
