"""Built-in checkers."""

from svlang.checkers.consistency import ConsistencyChecker
from svlang.checkers.svengelska import SvengelskaChecker
from svlang.checkers.compound import CompoundSplitter

__all__ = ["ConsistencyChecker", "SvengelskaChecker", "CompoundSplitter"]
