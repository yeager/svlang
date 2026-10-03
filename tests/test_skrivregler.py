from svlang.checkers.skrivregler import SkrivreglerChecker


def test_accepted_away_spellings_are_not_typos():
    checker = SkrivreglerChecker()
    assert checker.check('Ge dig iväg. Dra i väg reglaget. Iväg med dig!') == []
    assert any(h.suggestion == 'i så fall' for h in checker.check('isåfall'))


def test_tp_ordinal_suffix_is_not_split_email():
    c = SkrivreglerChecker()
    assert c.check('Visa den N:e posten, NUMMER:e posten och den 3:e posten.') == []
    hits = c.check('Läs e posten.')
    assert len(hits) == 1
    assert hits[0].suggestion == 'e-posten'


def test_contextual_word_pairs_are_not_sarskrivning():
    checker = SkrivreglerChecker()
    assert checker.check(
        'Program vara förberett. Det hände var dag. En bana för slaget.'
    ) == []


def test_line_break_after_de_is_not_an_indirect_object():
    checker = SkrivreglerChecker()
    assert checker.check('Visa de\n mest aktiva processerna.') == []


def test_comma_before_och_is_reported_by_default():
    checker = SkrivreglerChecker()
    issues = checker.check('Jag öppnade filen, och sparade ändringarna.')
    assert len(issues) == 1
    assert issues[0].rule == 'interpunktion'
    assert issues[0].suggestion == 'Ta bort kommat före ”och”'
    assert checker.check('Jag öppnade filen och sparade ändringarna.') == []


def test_swedish_punctuation_spacing_and_ellipsis_are_reported():
    checker = SkrivreglerChecker()
    issues = checker.check('Hej ! ( test ) Vänta...')
    assert {issue.suggestion for issue in issues} == {
        'Ta bort mellanslaget före skiljetecknet',
        'Ta bort mellanslaget innanför parentesen',
        'Använd ellipstecknet ”…” i stället för tre punkter',
    }
    assert checker.check('Hej! (test) Vänta…') == []


def test_swedish_quotes_numbers_percent_and_ranges_are_reported():
    checker = SkrivreglerChecker()
    text = '“Citat” 1.000.000 besökare, 8,65% mellan 11 - 12.'
    suggestions = {issue.suggestion for issue in checker.check(text)}
    assert suggestions == {
        'Använd svenska citattecken ”…”',
        'Gruppera stora tal med mellanslag, inte punkt',
        'Sätt mellanslag före procenttecknet',
        'Använd tankstreck i talintervall',
    }
    assert checker.check('”Citat” 1 000 000 besökare, 8,65 % mellan 11–12.') == []
