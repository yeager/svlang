from svlang.checkers.skrivregler import SkrivreglerChecker


def test_tp_ordinal_suffix_is_not_split_email():
    c = SkrivreglerChecker()
    assert c.check('Visa den N:e posten och den 3:e posten.') == []
    hits = c.check('Läs e posten.')
    assert len(hits) == 1
    assert hits[0].suggestion == 'e-posten'
