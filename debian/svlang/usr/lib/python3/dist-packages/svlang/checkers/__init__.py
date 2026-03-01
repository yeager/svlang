"""Built-in checkers."""

from svlang.checkers.consistency import ConsistencyChecker
from svlang.checkers.svengelska import SvengelskaChecker
from svlang.checkers.compound import CompoundSplitter
from svlang.checkers.lexicon import SwedishLexicon
from svlang.checkers.readability import LixCalculator

__all__ = ["ConsistencyChecker", "SvengelskaChecker", "CompoundSplitter", "SwedishLexicon", "LixCalculator"]
