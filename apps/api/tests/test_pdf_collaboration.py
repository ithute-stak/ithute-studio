import io

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.main import app


def _pdf() -> bytes:
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=(200, 300))
    pdf.drawString(30, 240, "Collaboration foundation")
    pdf.showPage()
    pdf.save()
    return output.getvalue()


def test_pdf_access_roles_and_webhook_outbox():
    with TestClient(app) as client:
        project = client.post(
            "/v1/pdf/projects",
            files={"file": ("collab.pdf", _pdf(), "application/pdf")},
        ).json()
        project_id = project["id"]

        grant = client.post(
            f"/v1/pdf/projects/{project_id}/access",
            json={
                "principalType": "user",
                "principalId": "user-123",
                "role": "editor",
            },
        )
        assert grant.status_code == 201
        grant_id = grant.json()["id"]
        assert grant.json()["role"] == "editor"
        assert client.get(f"/v1/pdf/projects/{project_id}/access").json()[0][
            "principalId"
        ] == "user-123"

        webhook = client.post(
            f"/v1/pdf/projects/{project_id}/webhooks",
            json={
                "endpoint": "https://example.com/ithute-hook",
                "events": ["pdf.updated"],
            },
        )
        assert webhook.status_code == 201
        webhook_id = webhook.json()["id"]
        assert webhook.json()["events"] == ["pdf.updated"]

        updated = client.put(
            f"/v1/pdf/projects/{project_id}",
            json={
                "expectedVersion": project["version"],
                "name": "Changed for webhook",
            },
        )
        assert updated.status_code == 200

        deliveries = client.get(
            f"/v1/pdf/projects/{project_id}/webhook-deliveries"
        )
        assert deliveries.status_code == 200
        assert len(deliveries.json()) == 1
        delivery = deliveries.json()[0]
        assert delivery["event"] == "pdf.updated"
        assert delivery["status"] == "pending"
        assert delivery["attemptCount"] == 0
        assert delivery["payload"]["projectId"] == project_id

        actions = {
            item["action"]
            for item in client.get(f"/v1/pdf/projects/{project_id}/audit").json()
        }
        assert "pdf.access.updated" in actions
        assert "pdf.webhook.created" in actions
        assert "pdf.updated" in actions

        assert (
            client.delete(f"/v1/pdf/projects/{project_id}/webhooks/{webhook_id}").status_code
            == 204
        )
        assert (
            client.delete(f"/v1/pdf/projects/{project_id}/access/{grant_id}").status_code
            == 204
        )
        assert client.delete(f"/v1/pdf/projects/{project_id}").status_code == 204
