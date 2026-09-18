from __future__ import annotations

import re
from copy import deepcopy
from datetime import date, datetime
from typing import Any
from uuid import uuid4

TOKEN_RE = re.compile(r"{{\s*([A-Za-z0-9_.-]+)\s*}}")


def get_path(data: dict[str, Any], path: str) -> Any:
    value: Any = data
    if not path:
        return value
    for part in path.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def format_value(
    value: Any,
    fmt: str | None = None,
    currency: str = "LSL",
) -> str:
    if value is None:
        return ""
    if fmt == "currency":
        try:
            return f"{currency} {float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)
    if fmt == "date":
        if isinstance(value, (date, datetime)):
            return value.strftime("%d %B %Y")
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime(
                "%d %B %Y"
            )
        except ValueError:
            return str(value)
    if fmt == "boolean":
        return "Yes" if bool(value) else "No"
    return str(value)


def _currency(data: dict[str, Any]) -> str:
    value = get_path(data, "document.currency")
    return str(value or "LSL").upper()


def _resolve_string(value: str, data: dict[str, Any]) -> str:
    def replacement(match: re.Match[str]) -> str:
        return format_value(get_path(data, match.group(1)), currency=_currency(data))

    return TOKEN_RE.sub(replacement, value)


def _resolve_value(value: Any, data: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return _resolve_string(value, data)
    if isinstance(value, list):
        return [_resolve_value(item, data) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_value(item, data) for key, item in value.items()}
    return value


def _text(value: str) -> dict[str, Any]:
    return {"type": "text", "text": value}


def _cell(value: str, header: bool = False) -> dict[str, Any]:
    return {
        "type": "tableHeader" if header else "tableCell",
        "content": [{"type": "paragraph", "content": [_text(value)]}],
    }


def resolve_node(node: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    kind = node.get("type")
    attrs = node.get("attrs") or {}
    if kind == "variable":
        return _text(
            format_value(
                get_path(data, str(attrs.get("path", ""))),
                attrs.get("format"),
                _currency(data),
            )
        )
    if kind == "dynamicTable":
        rows = get_path(data, str(attrs.get("collectionPath", "")))
        rows = rows if isinstance(rows, list) else []
        columns = attrs.get("columns") or []
        header = {
            "type": "tableRow",
            "content": [
                _cell(str(c.get("label", c.get("path", ""))), True) for c in columns
            ],
        }
        content = [header]
        for row in rows:
            item = row if isinstance(row, dict) else {"value": row}
            content.append(
                {
                    "type": "tableRow",
                    "content": [
                        _cell(
                            format_value(
                                get_path(item, str(c.get("path", ""))),
                                c.get("format"),
                                _currency(data),
                            )
                        )
                        for c in columns
                    ],
                }
            )
        return {"type": "table", "content": content}
    resolved = deepcopy(node)
    if "attrs" in resolved:
        resolved["attrs"] = _resolve_value(resolved.get("attrs") or {}, data)
    if kind == "text" and isinstance(resolved.get("text"), str):
        resolved["text"] = _resolve_string(str(resolved["text"]), data)
    if isinstance(node.get("content"), list):
        resolved["content"] = [resolve_node(child, data) for child in node["content"]]
    return resolved


def resolve_doc_json(
    document_json: dict[str, Any] | None,
    data: dict[str, Any],
) -> dict[str, Any]:
    doc = deepcopy(document_json or {"type": "doc", "content": []})
    return resolve_node(doc, data)


def generate_document(
    template: dict[str, Any],
    data: dict[str, Any],
    source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.now().astimezone().isoformat()
    document = deepcopy(template)
    document["schemaVersion"] = 1
    document["id"] = str(uuid4())
    document["header"] = resolve_doc_json(template.get("header"), data)
    document["body"] = resolve_doc_json(template.get("body"), data)
    document["footer"] = resolve_doc_json(template.get("footer"), data)
    document["variables"] = deepcopy(data)
    document["source"] = source
    document["createdAt"] = now
    document["updatedAt"] = now
    document["version"] = 1
    return document
