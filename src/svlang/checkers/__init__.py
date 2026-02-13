"""Built-in checkers."""

from svlang.checkers.consistency import ConsistencyChecker
from svlang.checkers.svengelska import SvengelskaChecker
from svlang.checkers.compound import CompoundSplitter
from svlang.checkers.lexicon import SwedishLexicon

__all__ = ["ConsistencyChecker", "SvengelskaChecker", "CompoundSplitter", "SwedishLexicon"]
