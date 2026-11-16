"""Extract user-facing Swedish text from TypeScript and TSX resources."""

from __future__ import annotations

import ast
import re
from html import unescape
from pathlib import Path


_TRANSLATION_VARIABLES = {
    "copy",
    "labels",
    "locale",
    "locales",
    "messages",
    "resources",
    "strings",
    "translation",
    "translations",
    "sv",
    "sv_se",
    "svse",
}
_TRANSLATION_CALLS = {
    "_", "$t", "gettext", "i18n.t", "msg", "ngettext", "t", "translate",
}
_MESSAGE_FIELDS = {"defaultmessage", "defaultvalue", "message"}
_VISIBLE_JSX_ATTRIBUTES = {
    "alt",
    "aria-label",
    "caption",
    "description",
    "label",
    "placeholder",
    "title",
    "tooltip",
}
_NON_TEXT_JSX_ATTRIBUTES = {
    "class",
    "classname",
    "id",
    "key",
    "name",
    "role",
    "src",
    "style",
    "type",
    "value",
}


class TypeScriptSupportUnavailable(RuntimeError):
    """Raised when TypeScript support is used without its optional parser."""


def _node_text(node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _string_value(node, source: bytes) -> str:
    raw = _node_text(node, source)
    if node.type == "template_string":
        pieces: list[str] = []
        for child in node.named_children:
            if child.type == "string_fragment":
                pieces.append(_decode_fragment(_node_text(child, source)))
            elif child.type == "template_substitution":
                # Retain a neutral word between surrounding prose so that a
                # placeholder does not create artificial spacing or punctuation.
                pieces.append("värde")
        return "".join(pieces)
    try:
        value = ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        value = raw[1:-1] if len(raw) >= 2 else raw
    return value if isinstance(value, str) else ""


def _decode_fragment(value: str) -> str:
    """Decode common JavaScript escapes without interpreting template syntax."""
    try:
        return ast.literal_eval('"' + value.replace('"', '\\"') + '"')
    except (SyntaxError, ValueError):
        return value


def _callee_name(node, source: bytes) -> str:
    raw = re.sub(r"\s+", "", _node_text(node, source))
    return raw


def _property_name(node, source: bytes) -> str:
    if node is None:
        return ""
    value = _node_text(node, source)
    if node.type in {"string", "template_string"}:
        value = _string_value(node, source)
    return value.strip().lower()


def _collect_object_values(
    node, source: bytes, output: list[str], *, message_fields_only: bool = False
) -> None:
    if node.type in {"string", "template_string"}:
        value = _string_value(node, source).strip()
        if value:
            output.append(value)
        return
    if node.type == "pair":
        key = _property_name(node.child_by_field_name("key"), source)
        value = node.child_by_field_name("value")
        if value is None:
            return
        if message_fields_only:
            if key in _MESSAGE_FIELDS:
                _collect_object_values(value, source, output)
        elif key not in {"comment", "context", "description", "id", "key", "source"}:
            _collect_object_values(value, source, output)
        return
    for child in node.named_children:
        _collect_object_values(child, source, output, message_fields_only=message_fields_only)


def _locale_module(path: Path) -> bool:
    locale_names = {"sv", "sv-se", "sv_se", "svse"}
    return path.stem.lower() in locale_names or any(
        part.lower() in locale_names for part in path.parts
    )


def extract_translation_text(path: Path, source_text: str) -> str:
    """Return likely translated values while excluding TypeScript syntax.

    Text is collected from recognized translation calls, translation/message
    objects, and user-visible JSX content. This intentionally does not inspect
    comments, identifiers, import paths, or arbitrary string constants.
    """
    try:
        import tree_sitter_typescript as ts_grammar
        from tree_sitter import Language, Parser
    except ImportError as exc:
        raise TypeScriptSupportUnavailable(
            "TypeScript analysis requires the optional dependencies; install svlang[typescript]."
        ) from exc

    source = source_text.encode("utf-8")
    language_factory = (
        ts_grammar.language_tsx
        if path.suffix.lower() == ".tsx"
        else ts_grammar.language_typescript
    )
    parser = Parser(Language(language_factory()))
    tree = parser.parse(source)
    output: list[str] = []
    locale_module = _locale_module(path)

    def visit(node) -> None:
        if node.type == "variable_declarator":
            name = _property_name(node.child_by_field_name("name"), source)
            value = node.child_by_field_name("value")
            if value is not None and (name in _TRANSLATION_VARIABLES or locale_module):
                if value.type in {"object", "array"}:
                    _collect_object_values(value, source, output)

        elif node.type == "call_expression":
            function = node.child_by_field_name("function")
            arguments = node.child_by_field_name("arguments")
            name = _callee_name(function, source) if function is not None else ""
            short_name = name.rsplit(".", 1)[-1]
            if arguments is not None and short_name in _TRANSLATION_CALLS:
                first = arguments.named_children[0] if arguments.named_children else None
                if first is not None:
                    if first.type in {"string", "template_string"}:
                        value = _string_value(first, source).strip()
                        if value:
                            output.append(value)
                    elif first.type in {"object", "array"}:
                        _collect_object_values(
                            first, source, output,
                            message_fields_only=short_name in {"msg", "translate"},
                        )
                for argument in arguments.named_children[1:]:
                    if argument.type == "object":
                        _collect_object_values(argument, source, output, message_fields_only=True)
            elif arguments is not None and short_name == "formatMessage":
                for argument in arguments.named_children:
                    if argument.type == "object":
                        _collect_object_values(argument, source, output, message_fields_only=True)

        elif node.type == "jsx_text":
            value = re.sub(r"\s+", " ", unescape(_node_text(node, source))).strip()
            if value:
                output.append(value)

        elif node.type == "jsx_attribute":
            name_node = node.child_by_field_name("name")
            value_node = node.child_by_field_name("value")
            attribute = _property_name(name_node, source)
            if (
                value_node is not None
                and attribute in _VISIBLE_JSX_ATTRIBUTES
                and attribute not in _NON_TEXT_JSX_ATTRIBUTES
                and value_node.type == "string"
            ):
                value = _string_value(value_node, source).strip()
                if value:
                    output.append(value)

        elif node.type == "jsx_expression" and len(node.named_children) == 1:
            expression = node.named_children[0]
            if expression.type in {"string", "template_string"}:
                value = _string_value(expression, source).strip()
                if value:
                    output.append(value)

        if locale_module and node.type == "export_statement":
            for child in node.named_children:
                if child.type in {"object", "array"}:
                    _collect_object_values(child, source, output)

        for child in node.named_children:
            visit(child)

    visit(tree.root_node)
    return "\n.\n".join(output)
