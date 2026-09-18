import base64
import io

from fastapi.testclient import TestClient
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from app.main import app


ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Zl1sAAAAASUVORK5CYII="
)


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


def _encrypted_pdf(password: str) -> bytes:
    reader = PdfReader(io.BytesIO(_sample_pdf()))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_pdf_platform_foundation_upload_revision_asset_restore_and_export():
    with TestClient(app) as client:
        created = client.post(
            "/v1/pdf/projects",
            files={"file": ("sample.pdf", _sample_pdf(), "application/pdf")},
            data={"name": "Editable sample"},
        )
        assert created.status_code == 201
        project = created.json()
        project_id = project["id"]
        assert project["schemaVersion"] == 1
        assert project["status"] == "draft"
        assert project["pageCount"] == 2
        assert project["pageOrder"] == [0, 1]
        assert len(project["sourceSha256"]) == 64
        assert project["sourceSize"] > 100
        assert project["importState"]["coordinateSpace"] == "pdf-points-top-left"
        assert project["security"]["encrypted"] is False
        assert any(item["type"] == "text" for item in project["objectIndex"])
        assert project["fontCatalog"]

        preview = client.get(f"/v1/pdf/projects/{project_id}/pages/0/preview")
        assert preview.status_code == 200
        assert preview.headers["content-type"].startswith("image/png")
        assert preview.content.startswith(b"\x89PNG")

        extracted = client.get(f"/v1/pdf/projects/{project_id}/pages/0/text")
        assert extracted.status_code == 200
        assert any(
            "Editable PDF text" in item["text"]
            for item in extracted.json()["items"]
        )

        indexed = client.get(f"/v1/pdf/projects/{project_id}/pages/0/objects")
        assert indexed.status_code == 200
        assert indexed.json()["coordinateSpace"] == "pdf-points-top-left"
        assert any(
            "Editable PDF text" in item.get("text", "")
            for item in indexed.json()["items"]
        )

        revisions = client.get(f"/v1/pdf/projects/{project_id}/revisions")
        assert revisions.status_code == 200
        assert [item["version"] for item in revisions.json()] == [1]

        jobs = client.get(f"/v1/pdf/projects/{project_id}/jobs")
        assert jobs.status_code == 200
        assert jobs.json()[0]["kind"] == "import"
        assert jobs.json()[0]["status"] == "completed"

        audit = client.get(f"/v1/pdf/projects/{project_id}/audit")
        assert audit.status_code == 200
        assert audit.json()[0]["action"] == "pdf.uploaded"

        asset = client.post(
            f"/v1/pdf/projects/{project_id}/assets",
            files={"file": ("pixel.png", ONE_PIXEL_PNG, "image/png")},
        )
        assert asset.status_code == 201
        asset_id = asset.json()["id"]
        assert len(asset.json()["sha256"]) == 64
        downloaded_asset = client.get(
            f"/v1/pdf/projects/{project_id}/assets/{asset_id}"
        )
        assert downloaded_asset.status_code == 200
        assert downloaded_asset.content == ONE_PIXEL_PNG

        saved = client.put(
            f"/v1/pdf/projects/{project_id}",
            json={
                "expectedVersion": project["version"],
                "status": "review",
                "pageOrder": [1, 0],
                "metadata": {
                    "title": "Edited PDF",
                    "author": "Ithute Studio",
                    "keywords": ["studio", "pdf"],
                    "custom": {},
                },
                "objects": [
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
        saved_project = saved.json()
        assert saved_project["version"] == project["version"] + 1
        assert saved_project["status"] == "review"
        assert saved_project["pageOrder"] == [1, 0]
        assert saved_project["objects"][0]["id"] == "replacement-1"
        assert saved_project["edits"] == saved_project["objects"]

        revisions = client.get(f"/v1/pdf/projects/{project_id}/revisions")
        assert revisions.status_code == 200
        assert [item["version"] for item in revisions.json()] == [2, 1]

        restored = client.post(
            f"/v1/pdf/projects/{project_id}/revisions/1/restore",
            json={"expectedVersion": saved_project["version"]},
        )
        assert restored.status_code == 200
        restored_project = restored.json()
        assert restored_project["version"] == 3
        assert restored_project["status"] == "draft"
        assert restored_project["pageOrder"] == [0, 1]
        assert restored_project["objects"] == []

        exported = client.post(
            f"/v1/pdf/projects/{project_id}/export",
            json={"profile": "web"},
        )
        assert exported.status_code == 200
        assert exported.headers["content-type"].startswith("application/pdf")
        assert exported.content.startswith(b"%PDF")
        assert len(exported.content) > 1000

        jobs = client.get(f"/v1/pdf/projects/{project_id}/jobs").json()
        assert any(item["kind"] == "export" for item in jobs)
        audit = client.get(f"/v1/pdf/projects/{project_id}/audit").json()
        actions = {item["action"] for item in audit}
        assert "pdf.revision.restored" in actions
        assert "pdf.exported" in actions
        assert "pdf.asset.added" in actions

        removed_asset = client.delete(
            f"/v1/pdf/projects/{project_id}/assets/{asset_id}"
        )
        assert removed_asset.status_code == 204

        deleted = client.delete(f"/v1/pdf/projects/{project_id}")
        assert deleted.status_code == 204


def test_pdf_rejects_non_pdf_upload():
    with TestClient(app) as client:
        response = client.post(
            "/v1/pdf/projects",
            files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
        )
        assert response.status_code == 400


def test_password_protected_pdf_requires_password_and_is_normalized_on_import():
    content = _encrypted_pdf("secret123")
    with TestClient(app) as client:
        rejected = client.post(
            "/v1/pdf/projects",
            files={"file": ("encrypted.pdf", content, "application/pdf")},
        )
        assert rejected.status_code == 400
        assert "password protected" in rejected.json()["detail"].lower()

        accepted = client.post(
            "/v1/pdf/projects",
            files={"file": ("encrypted.pdf", content, "application/pdf")},
            data={"password": "secret123"},
        )
        assert accepted.status_code == 201
        project = accepted.json()
        assert project["security"]["encrypted"] is True
        assert project["security"]["decryptedOnImport"] is True
        assert project["sourceSize"] > 100
        assert client.delete(f"/v1/pdf/projects/{project['id']}").status_code == 204


def test_pdf_lifecycle_rejects_skipping_approval_states():
    with TestClient(app) as client:
        created = client.post(
            "/v1/pdf/projects",
            files={"file": ("sample.pdf", _sample_pdf(), "application/pdf")},
        ).json()
        project_id = created["id"]
        response = client.put(
            f"/v1/pdf/projects/{project_id}",
            json={"expectedVersion": created["version"], "status": "signed"},
        )
        assert response.status_code == 400
        assert "cannot move" in response.json()["detail"]
        assert client.delete(f"/v1/pdf/projects/{project_id}").status_code == 204
