"""Consistency checker — find same source translated differently."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Inconsistency:
    """A source string with multiple different translations."""
    source: str
    translations: dict[str, list[str]]  # translation → list of locations
    

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
        # source → {translation → [locations]}
        self._entries: dict[str, dict[str, list[str]]] = {}

    def _normalize(self, text: str) -> str:
        if self._case_sensitive:
            return text
        return text.lower()

    def add(self, source: str, translation: str, location: str = "") -> None:
        """Register a source→translation pair."""
        key = self._normalize(source)
        if key not in self._entries:
            self._entries[key] = {}
        norm_trans = self._normalize(translation)
        if norm_trans not in self._entries[key]:
            self._entries[key][norm_trans] = []
        self._entries[key][norm_trans].append(location)

    def check(self) -> list[Inconsistency]:
        """Return all source strings with inconsistent translations."""
        issues = []
        for source, translations in self._entries.items():
            if len(translations) > 1:
                issues.append(Inconsistency(source=source, translations=translations))
        issues.sort(key=lambda i: i.source)
        return issues

    def add_po_file(self, path: str) -> None:
        """Load entries from a .po file (requires polib)."""
        import polib
        po = polib.pofile(path)
        for entry in po.translated_entries():
            loc = f"{path}:{entry.linenum}" if hasattr(entry, 'linenum') else path
            self.add(entry.msgid, entry.msgstr, loc)

    def add_ts_file(self, path: str) -> None:
        """Load entries from a Qt .ts file."""
        import xml.etree.ElementTree as ET
        tree = ET.parse(path)
        for msg in tree.findall('.//message'):
            src = msg.findtext('source', '')
            trans = msg.findtext('translation', '')
            if src and trans:
                loc_elem = msg.find('location')
                loc = f"{path}"
                if loc_elem is not None:
                    loc = f"{loc_elem.get('filename', path)}:{loc_elem.get('line', '')}"
                self.add(src, trans, loc)
