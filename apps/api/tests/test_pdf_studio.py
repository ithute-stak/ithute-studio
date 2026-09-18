import io

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.main import app


def _sample_pdf() -> bytes:
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=(300, 400))
    pdf.setFont("Helvetica", 14)
    pdf.drawString(40, 330, "Editable PDF text")
    pdf.rect(35, 250, 120, 40, fill=0, stroke=1)
    pdf.showPage()
    pdf.setFont("Helvetica", 12)
    pdf.drawString(40, 330, "Second page")
    pdf.showPage()
    pdf.save()
    return output.getvalue()


def test_pdf_upload_extract_edit_and_backend_export():
    with TestClient(app) as client:
        created = client.post(
            "/v1/pdf/projects",
            files={"file": ("sample.pdf", _sample_pdf(), "application/pdf")},
            data={"name": "Editable sample"},
        )
        assert created.status_code == 201
        project = created.json()
        project_id = project["id"]
        assert project["pageCount"] == 2
        assert project["pageOrder"] == [0, 1]

        preview = client.get(f"/v1/pdf/projects/{project_id}/pages/0/preview")
        assert preview.status_code == 200
        assert preview.headers["content-type"].startswith("image/png")
        assert preview.content.startswith(b"\x89PNG")

        extracted = client.get(f"/v1/pdf/projects/{project_id}/pages/0/text")
        assert extracted.status_code == 200
        assert any("Editable PDF text" in item["text"] for item in extracted.json()["items"])

        saved = client.put(
            f"/v1/pdf/projects/{project_id}",
            json={
                "expectedVersion": project["version"],
                "pageOrder": [1, 0],
                "edits": [
                    {
                        "id": "replacement-1",
                        "page": 0,
                        "type": "text",
                        "x": 40,
                        "y": 55,
                        "width": 150,
                        "height": 22,
                        "text": "Changed in Ithute Studio",
                        "fontSize": 13,
                        "fontFamily": "Helvetica",
                        "color": "#111111",
                        "fill": "#ffffff",
                        "eraseOriginal": True,
                    }
                ],
            },
        )
        assert saved.status_code == 200
        assert saved.json()["version"] == project["version"] + 1
        assert saved.json()["pageOrder"] == [1, 0]

        exported = client.post(f"/v1/pdf/projects/{project_id}/export")
        assert exported.status_code == 200
        assert exported.headers["content-type"].startswith("application/pdf")
        assert exported.content.startswith(b"%PDF")
        assert len(exported.content) > 1000

        deleted = client.delete(f"/v1/pdf/projects/{project_id}")
        assert deleted.status_code == 204


def test_pdf_rejects_non_pdf_upload():
    with TestClient(app) as client:
        response = client.post(
            "/v1/pdf/projects",
            files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
        )
        assert response.status_code == 400
