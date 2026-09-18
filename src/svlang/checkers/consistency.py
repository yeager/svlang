"""Consistency checker — find same source translated differently."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Inconsistency:
    """A source string with multiple different translations."""
    source: str
    translations: dict[str, list[str]]  # translation → list of locations
    context: str = ""
    plural_source: str = ""
    plural_index: int | None = None
    disambiguation: str = ""
    

class ConsistencyChecker:
    """Check that identical source strings have identical translations.
    
    Usage:
        checker = ConsistencyChecker()
        checker.add("Save", "Spara", "file_menu.po:12")
        checker.add("Save", "Lagra", "other.po:45")
        issues = checker.check()
        # → [Inconsistency(source="Save", translations={"Spara": [...], "Lagra": [...]})]
    """

    def __init__(self, *, case_sensitive: bool = True):
        self._case_sensitive = case_sensitive
        # A message identity includes context and the particular plural form.
        self._entries: dict[tuple, dict[str, list[str]]] = {}

    def _normalize(self, text: str) -> str:
        if self._case_sensitive:
            return text
        return text.lower()

    def add(self, source: str, translation: str, location: str = "", *,
            context: str = "", plural_source: str = "",
            plural_index: int | None = None, disambiguation: str = "") -> None:
        """Register a source→translation pair."""
        key = (self._normalize(source), context,
               self._normalize(plural_source), plural_index, disambiguation)
        if key not in self._entries:
            self._entries[key] = {}
        norm_trans = self._normalize(translation)
        if norm_trans not in self._entries[key]:
            self._entries[key][norm_trans] = []
        self._entries[key][norm_trans].append(location)

    def check(self) -> list[Inconsistency]:
        """Return all source strings with inconsistent translations."""
        issues = []
        for key, translations in self._entries.items():
            if len(translations) > 1:
                source, context, plural_source, plural_index, disambiguation = key
                issues.append(Inconsistency(source, translations, context,
                                            plural_source, plural_index, disambiguation))
        issues.sort(key=lambda i: (i.source, i.context, i.plural_source,
                                  -1 if i.plural_index is None else i.plural_index,
                                  i.disambiguation))
        return issues

    def add_po_file(self, path: str) -> None:
        """Load entries from a .po file (requires polib)."""
        import polib
        po = polib.pofile(path)
        for entry in po.translated_entries():
            loc = f"{path}:{entry.linenum}" if hasattr(entry, 'linenum') else path
            if entry.msgid_plural:
                for index, value in sorted(entry.msgstr_plural.items()):
                    self.add(entry.msgid, value, loc, context=entry.msgctxt or "",
                             plural_source=entry.msgid_plural, plural_index=index)
            else:
                self.add(entry.msgid, entry.msgstr, loc, context=entry.msgctxt or "")

    def add_ts_file(self, path: str) -> None:
        """Load entries from a Qt .ts file."""
        import xml.etree.ElementTree as ET
        tree = ET.parse(path)
        for context in tree.findall('.//context'):
            name = context.findtext('name', '')
            for msg in context.findall('message'):
                src = msg.findtext('source', '')
                trans = msg.find('translation')
                if not src or trans is None or trans.get('type') in {'unfinished', 'vanished', 'obsolete'}:
                    continue
                forms = trans.findall('numerusform') if msg.get('numerus') == 'yes' else [trans]
                values = [''.join(form.itertext()) for form in forms]
                if not values or any(not value.strip() for value in values):
                    continue
                loc_elem = msg.find('location')
                loc = f"{path}"
                if loc_elem is not None:
                    loc = f"{loc_elem.get('filename', path)}:{loc_elem.get('line', '')}"
                for index, value in enumerate(values):
                    self.add(src, value, loc, context=name,
                             plural_index=index if msg.get('numerus') == 'yes' else None,
                             disambiguation=msg.findtext('comment', ''))
