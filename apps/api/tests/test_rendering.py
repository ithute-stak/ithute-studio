from app.document_renderer import render_docx, render_pdf


def sample():
    return {"schemaVersion":1,"properties":{"title":"Render Test","author":"Studio"},"settings":{"pageSize":"a4","orientation":"portrait","marginsMm":{"top":20,"right":20,"bottom":20,"left":20},"pageNumbering":{"enabled":True},"watermark":{"text":"DRAFT","opacity":0.08,"rotation":-35}},"header":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Header"}]}]},"footer":{"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Footer"}]}]},"body":{"type":"doc","content":[{"type":"heading","attrs":{"level":1},"content":[{"type":"text","text":"Title"}]},{"type":"paragraph","content":[{"type":"text","text":"Hello world","marks":[{"type":"bold"}]}]},{"type":"table","content":[{"type":"tableRow","content":[{"type":"tableHeader","content":[{"type":"paragraph","content":[{"type":"text","text":"A"}]}]},{"type":"tableHeader","content":[{"type":"paragraph","content":[{"type":"text","text":"B"}]}]}]},{"type":"tableRow","content":[{"type":"tableCell","content":[{"type":"paragraph","content":[{"type":"text","text":"1"}]}]},{"type":"tableCell","content":[{"type":"paragraph","content":[{"type":"text","text":"2"}]}]}]}]},{"type":"qrCode","attrs":{"value":"https://example.test/verify"}}]}}


def test_pdf_render():
    data = render_pdf(sample())
    assert data.startswith(b"%PDF")
    assert len(data) > 1000


def test_docx_render():
    data = render_docx(sample())
    assert data.startswith(b"PK")
    assert len(data) > 1000
