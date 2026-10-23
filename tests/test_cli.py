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


def test_skrivregler_po_ignores_source_defined_cli_alignment(tmp_path, capsys):
    po = tmp_path / "sv.po"
    po.write_text(
        'msgid "-p      Print status"\n'
        'msgstr "-p      Skriv ut status"\n\n'
        'msgid "Vanlig text"\n'
        'msgstr "Vanlig  text"\n',
        encoding="utf-8",
    )
    assert main(["skrivregler", "--file", str(po), "--enable-interpunktion"]) == 1
    output = capsys.readouterr().out
    assert output.count("Dubbelt mellanslag") == 1


def test_skrivregler_po_ignores_source_defined_em_dash(tmp_path, capsys):
    po = tmp_path / "sv.po"
    po.write_text(
        'msgid "Status — clear"\n'
        'msgstr "Status — klar"\n\n'
        'msgid "Plain text"\n'
        'msgstr "Status — fortfarande fel"\n',
        encoding="utf-8",
    )
    assert main(["skrivregler", "--file", str(po), "--enable-interpunktion"]) == 1
    output = capsys.readouterr().out
    assert output.count("Undvik tankstreck") == 1


def test_skrivregler_po_ignores_source_defined_cli_punctuation(tmp_path, capsys):
    po = tmp_path / "sv.po"
    po.write_text(
        'msgid "cmd [argument ...] ; ( expression ) ?"\n'
        'msgstr "cmd [argument ...] ; ( uttryck ) ?"\n\n'
        'msgid "Vanlig text"\n'
        'msgstr "Vanlig ... text"\n',
        encoding="utf-8",
    )
    assert main(["skrivregler", "--file", str(po), "--enable-interpunktion"]) == 1
    output = capsys.readouterr().out
    assert output.count("ellipstecknet") == 1


def test_check_fluent_analyzes_values_without_keys_or_variables(tmp_path, capsys):
    catalog = tmp_path / "sv.ftl"
    catalog.write_text(
        'swedish-key = Hej och välkommen {"["}{$name}\n',
        encoding="utf-8",
    )
    main(["--json", "check", "--file", str(catalog)])
    data = json.loads(capsys.readouterr().out)
    assert data["rare_words"] == []


def test_skrivregler_fluent_checks_target_values(tmp_path, capsys):
    catalog = tmp_path / "sv.ftl"
    catalog.write_text(
        'swedish-key = Hej, och välkommen {"["}{$name}\n',
        encoding="utf-8",
    )
    assert main(["skrivregler", "--file", str(catalog)]) == 1
    assert "Ta bort kommat före ”och”" in capsys.readouterr().out


def test_skrivregler_fluent_ignores_cli_usage_ellipsis(tmp_path, capsys):
    catalog = tmp_path / "sv.ftl"
    catalog.write_text(
        'tool-usage = verktyg [FLAGGA]... [FIL]...\n', encoding="utf-8"
    )
    assert main(["skrivregler", "--file", str(catalog)]) == 0
    assert "ellipstecknet" not in capsys.readouterr().out


def test_skrivregler_fluent_keeps_variables_from_creating_spacing_errors(tmp_path, capsys):
    catalog = tmp_path / "sv.ftl"
    catalog.write_text('error = fel: {$name}: detalj\n', encoding="utf-8")
    assert main(["skrivregler", "--file", str(catalog)]) == 0
    assert "Interpunktion" not in capsys.readouterr().out


def test_skrivregler_directory_checks_localization_catalogs(tmp_path, capsys):
    catalog_dir = tmp_path / "catalogs"
    catalog_dir.mkdir()
    (catalog_dir / "sv.ftl").write_text(
        "message = Hej, och välkommen\n", encoding="utf-8"
    )
    (catalog_dir / "notes.txt").write_text(
        "Hej, och detta är inte en katalog.\n", encoding="utf-8"
    )
    assert main(["skrivregler", "--file", str(catalog_dir)]) == 1
    output = capsys.readouterr().out
    assert "Ta bort kommat före ”och”" in output


def test_skrivregler_directory_without_catalogs_is_an_error(tmp_path, capsys):
    assert main(["skrivregler", "--file", str(tmp_path)]) == 2
    assert "No localization files found" in capsys.readouterr().err


def test_skrivregler_xliff_checks_targets_not_xml_indentation(tmp_path, capsys):
    catalog = tmp_path / "sv.xliff"
    catalog.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2">
  <file source-language="en" target-language="sv">
    <body>
      <trans-unit id="one">
        <source>English, and source</source>
        <target>Hej och välkommen</target>
      </trans-unit>
      <trans-unit id="two">
        <source>More English source text</source>
        <target>Detta, och det andra</target>
      </trans-unit>
    </body>
  </file>
</xliff>
""",
        encoding="utf-8",
    )
    assert main(["skrivregler", "--file", str(catalog), "--enable-interpunktion"]) == 1
    output = capsys.readouterr().out
    assert "Ta bort kommat före ”och”" in output
    assert "Dubbelt mellanslag" not in output

def test_frequency_miss_is_not_a_spelling_verdict(capsys):
    assert main(["freq", "välkommen"]) == 0
    assert "Status: Okänt ord" not in capsys.readouterr().out
