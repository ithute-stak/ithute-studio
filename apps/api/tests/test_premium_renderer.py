from app.premium_renderer import render_docx, render_html, render_pdf


def sample_document() -> dict:
    return {
        "schemaVersion": 1,
        "id": "premium-render-test",
        "workspaceId": "system",
        "properties": {"title": "Premium Invoice", "author": "Ithute Studio"},
        "settings": {
            "pageSize": "a4",
            "orientation": "portrait",
            "marginsMm": {"top": 20, "right": 18, "bottom": 18, "left": 18},
            "columns": 1,
            "headerDistanceMm": 8,
            "footerDistanceMm": 8,
            "showRulers": True,
            "pageNumbering": {"enabled": True, "startAt": 1, "format": "1", "position": "footer"},
        },
        "design": {
            "primaryColor": "#102A43",
            "secondaryColor": "#D9EAF7",
            "accentColor": "#2F80ED",
            "textColor": "#172B4D",
            "mutedColor": "#627D98",
            "borderColor": "#BCCCDC",
            "fontFamily": "Helvetica",
            "headerStyle": "band",
            "footerStyle": "line",
            "documentLabel": "Invoice",
        },
        "header": {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Example Company (Pty) Ltd"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "INVOICE"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "REG-2026-001"}]},
            ],
        },
        "body": {
            "type": "doc",
            "content": [
                {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": "Invoice"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "Professional branded document."}]},
            ],
        },
        "footer": {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Maseru, Lesotho"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "info@example.test"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "Verify ITH-TEST"}]},
            ],
        },
        "variables": {"company": {"name": "Example Company (Pty) Ltd"}},
        "createdAt": "2026-09-18T00:00:00+00:00",
        "updatedAt": "2026-09-18T00:00:00+00:00",
        "version": 1,
    }


def test_premium_renderer_adds_brand_to_all_formats() -> None:
    document = sample_document()

    pdf = render_pdf(document)
    docx = render_docx(document)
    html = render_html(document)

    assert pdf.startswith(b"%PDF")
    assert docx.startswith(b"PK")
    assert 'class="ithute-brand-lockup"' in html
    assert "data:image/png;base64," in html


def test_premium_renderer_uses_monogram_when_logo_is_missing() -> None:
    html = render_html(sample_document())
    assert "Company logo" in html
    assert "Premium Invoice" in html
