from __future__ import annotations
from html import escape
from typing import Any


def attrs(node: dict[str, Any]) -> dict[str, Any]:
    return node.get("attrs") or {}


def render_node(node: dict[str, Any]) -> str:
    kind = node.get("type")
    content = "".join(render_node(child) for child in node.get("content") or [])
    a = attrs(node)
    if kind == "doc": return content
    if kind == "text":
        text = escape(str(node.get("text", "")))
        for mark in node.get("marks") or []:
            t = mark.get("type")
            if t == "bold": text = f"<strong>{text}</strong>"
            elif t == "italic": text = f"<em>{text}</em>"
            elif t == "underline": text = f"<u>{text}</u>"
            elif t == "link": text = f'<a href="{escape(str((mark.get("attrs") or {}).get("href", "")))}">{text}</a>'
        return text
    if kind == "paragraph": return f"<p>{content or '<br>'}</p>"
    if kind == "heading": return f"<h{int(a.get('level', 1))}>{content}</h{int(a.get('level', 1))}>"
    if kind == "bulletList": return f"<ul>{content}</ul>"
    if kind == "orderedList": return f"<ol>{content}</ol>"
    if kind == "listItem": return f"<li>{content}</li>"
    if kind == "blockquote": return f"<blockquote>{content}</blockquote>"
    if kind == "horizontalRule": return "<hr>"
    if kind == "hardBreak": return "<br>"
    if kind == "pageBreak": return '<div class="page-break"></div>'
    if kind == "table": return f"<table>{content}</table>"
    if kind == "tableRow": return f"<tr>{content}</tr>"
    if kind == "tableHeader": return f"<th>{content}</th>"
    if kind == "tableCell": return f"<td>{content}</td>"
    if kind == "image": return f'<img src="{escape(str(a.get("src", "")))}" alt="{escape(str(a.get("alt", "")))}">'
    if kind in {"signature", "stamp", "qrCode", "chart", "textBox"}:
        return f'<div class="studio-object studio-{kind}">{escape(str(a.get("label") or kind))}</div>'
    return content


def render_html(document: dict[str, Any]) -> str:
    settings = document.get("settings") or {}
    margins = settings.get("marginsMm") or {"top": 20, "right": 20, "bottom": 20, "left": 20}
    body = render_node(document.get("body") or {"type":"doc","content":[]})
    header = render_node(document.get("header") or {"type":"doc","content":[]})
    footer = render_node(document.get("footer") or {"type":"doc","content":[]})
    title = escape(str((document.get("properties") or {}).get("title", "Document")))
    css = f'''@page{{margin:{margins.get('top',20)}mm {margins.get('right',20)}mm {margins.get('bottom',20)}mm {margins.get('left',20)}mm}}body{{font-family:Arial,sans-serif;line-height:1.45;color:#111}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #aaa;padding:6px;vertical-align:top}}img{{max-width:100%}}.page-break{{break-after:page}}header,footer{{font-size:10pt;color:#555}}.studio-object{{border:1px dashed #777;padding:10px;margin:8px 0}}'''
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{css}</style></head><body><header>{header}</header><main>{body}</main><footer>{footer}</footer></body></html>"
