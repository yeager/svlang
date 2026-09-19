import json
from svlang.cli import main


def test_lookup_plain_output(capsys):
    assert main(['lookup', 'hund']) == 0
    output = capsys.readouterr().out
    assert 'hund' in output and 'dog' in output


def test_lookup_json_and_missing_word(capsys):
    assert main(['--json', 'lookup', 'hund']) == 0
    assert json.loads(capsys.readouterr().out)['found'] is True
    assert main(['lookup', 'osannolikttestordxyz']) == 1
    assert 'osannolikttestordxyz' in capsys.readouterr().out


def test_about_license_matches_distribution(capsys):
    assert main(['--about']) == 0
    output = capsys.readouterr().out
    assert 'MIT' in output and 'GPL' not in output


def test_consistency_missing_input_is_an_error(tmp_path, capsys):
    assert main(['consistency', str(tmp_path / 'missing.po')]) == 2
    result = capsys.readouterr()
    assert 'consistent' not in result.out
    assert 'missing.po' in result.err


def test_consistency_json_parse_error(tmp_path, capsys):
    path = tmp_path / 'broken.ts'
    path.write_text('<TS><context>')
    assert main(['--json', 'consistency', str(path)]) == 2
    assert json.loads(capsys.readouterr().out)['errors']


def test_check_known_words_without_hunspell(monkeypatch, capsys):
    from svlang.checkers import frequency
    monkeypatch.setattr(frequency.shutil, "which", lambda _: None)
    assert main(["--json", "check", "--text", "Välkommen abstinensprocess qzxqzxqzx"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [r["word"] for r in data["rare_words"]] == ["qzxqzxqzx"]


def test_check_po_analyzes_targets_not_english_source(tmp_path, capsys):
    po = tmp_path / "sv.po"
    po.write_text(
        'msgid "EnglishSourceOnly qzxqzxqzx"\n'
        'msgstr "Välkommen"\n',
        encoding="utf-8",
    )
    assert main(["--json", "check", "--file", str(po)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["rare_words"] == []


def test_check_po_keeps_entries_as_separate_sentences(tmp_path, capsys):
    po = tmp_path / "sv.po"
    po.write_text(
        'msgid "one"\nmsgstr "Första etiketten"\n\n'
        'msgid "two"\nmsgstr "Andra etiketten"\n',
        encoding="utf-8",
    )
    assert main(["--json", "check", "--file", str(po)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["statistics"]["sentence_count"] == 2


def test_frequency_miss_is_not_a_spelling_verdict(capsys):
    assert main(["freq", "välkommen"]) == 0
    assert "Status: Okänt ord" not in capsys.readouterr().out
