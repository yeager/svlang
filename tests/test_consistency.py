"""Tests for the consistency checker."""

from svlang.checkers.consistency import ConsistencyChecker
import polib


def write_po(path, entries):
    po = polib.POFile()
    po.metadata = {'Language': 'sv', 'Plural-Forms': 'nplurals=2; plural=(n != 1);'}
    po.extend(entries)
    po.save(str(path))
    return str(path)


def test_po_contexts_and_plural_forms(tmp_path):
    a = write_po(tmp_path / 'a.po', [
        polib.POEntry(msgid='Open', msgstr='Öppna', msgctxt='action'),
        polib.POEntry(msgid='Open', msgstr='Öppen', msgctxt='state'),
        polib.POEntry(msgid='%d file', msgid_plural='%d files',
                      msgstr_plural={0: '%d fil', 1: '%d filer'}),
    ])
    b = write_po(tmp_path / 'b.po', [
        polib.POEntry(msgid='Open', msgstr='Öppna', msgctxt='action'),
        polib.POEntry(msgid='%d file', msgid_plural='%d files',
                      msgstr_plural={0: '%d fil', 1: '%d arkiv'}),
        polib.POEntry(msgid='Open', msgstr='Starta', msgctxt='action', flags=['fuzzy']),
        polib.POEntry(msgid='Open', msgstr='Gammal', msgctxt='action', obsolete=True),
    ])
    c = ConsistencyChecker()
    c.add_po_file(a)
    c.add_po_file(b)
    issues = c.check()
    assert len(issues) == 1
    assert issues[0].plural_source == '%d files'
    assert issues[0].plural_index == 1
    assert set(issues[0].translations) == {'%d filer', '%d arkiv'}


def test_different_plural_sources_do_not_conflict(tmp_path):
    path = write_po(tmp_path / 'plural.po', [
        polib.POEntry(msgid='One', msgid_plural='Files', msgstr_plural={0: 'En', 1: 'Filer'}),
        polib.POEntry(msgid='One', msgid_plural='Folders', msgstr_plural={0: 'En', 1: 'Mappar'}),
    ])
    c = ConsistencyChecker()
    c.add_po_file(path)
    assert c.check() == []


def test_ts_contexts_disambiguation_plurals_and_inactive_messages(tmp_path):
    path = tmp_path / 'sv.ts'
    path.write_text('''<TS language="sv"><context><name>Menu</name>
      <message><source>Open</source><translation>Öppna</translation></message>
      <message><source>Open</source><comment>state</comment><translation>Öppen</translation></message>
      <message><source>Open</source><translation type="unfinished">Starta</translation></message>
      <message><source>Open</source><translation type="vanished">Visa</translation></message>
      <message><source>Open</source><translation type="obsolete">Gammal</translation></message>
      <message numerus="yes"><source>%n file(s)</source><translation>
        <numerusform>%n fil</numerusform><numerusform>%n filer</numerusform>
      </translation></message>
      <message numerus="yes"><source>%n file(s)</source><translation>
        <numerusform>%n fil</numerusform><numerusform>%n arkiv</numerusform>
      </translation></message>
      </context><context><name>Status</name>
      <message><source>Open</source><translation>Öppen</translation></message>
      </context></TS>''', encoding='utf-8')
    c = ConsistencyChecker()
    c.add_ts_file(str(path))
    issues = c.check()
    assert len(issues) == 1
    assert issues[0].context == 'Menu'
    assert issues[0].plural_index == 1
    assert set(issues[0].translations) == {'%n filer', '%n arkiv'}


def test_detects_inconsistency():
    c = ConsistencyChecker()
    c.add("Save", "Spara", "a.po:1")
    c.add("Save", "Lagra", "b.po:5")
    issues = c.check()
    assert len(issues) == 1
    assert "spara" in issues[0].translations or "Spara" in issues[0].translations


def test_consistent_ok():
    c = ConsistencyChecker()
    c.add("Save", "Spara", "a.po:1")
    c.add("Save", "Spara", "b.po:5")
    assert c.check() == []


def test_case_insensitive():
    c = ConsistencyChecker(case_sensitive=False)
    c.add("Save", "Spara", "a.po:1")
    c.add("Save", "spara", "b.po:5")
    assert c.check() == []


def test_case_sensitive():
    c = ConsistencyChecker(case_sensitive=True)
    c.add("Save", "Spara", "a.po:1")
    c.add("Save", "spara", "b.po:5")
    assert len(c.check()) == 1


def test_multiple_sources():
    c = ConsistencyChecker()
    c.add("Open", "Öppna", "a.po:1")
    c.add("Save", "Spara", "a.po:2")
    c.add("Save", "Lagra", "b.po:3")
    issues = c.check()
    assert len(issues) == 1
    assert issues[0].source == "Save"
