from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx


class IthuteDocumentStudioClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    @property
    def headers(self) -> dict[str, str]:
        return {"authorization": f"Bearer {self.token}"} if self.token else {}

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        headers = {**self.headers, **kwargs.pop("headers", {})}
        response = httpx.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            timeout=60,
            **kwargs,
        )
        response.raise_for_status()
        return response

    def generate_from_template(
        self,
        template: dict[str, Any],
        data: dict[str, Any],
        source: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/documents/from-template",
            json={"template": template, "data": data, "source": source},
        ).json()

    def list_pdf_projects(self) -> list[dict[str, Any]]:
        return self._request("GET", "/v1/pdf/projects").json()

    def get_pdf_project(self, project_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/pdf/projects/{project_id}").json()

    def upload_pdf(
        self,
        path: str | Path,
        *,
        name: str | None = None,
        workspace_id: str | None = None,
        password: str | None = None,
    ) -> dict[str, Any]:
        file_path = Path(path)
        data = {
            key: value
            for key, value in {
                "name": name,
                "workspaceId": workspace_id,
                "password": password,
            }.items()
            if value is not None
        }
        with file_path.open("rb") as handle:
            return self._request(
                "POST",
                "/v1/pdf/projects",
                data=data,
                files={"file": (file_path.name, handle, "application/pdf")},
            ).json()

    def save_pdf_project(
        self,
        project_id: str,
        update: dict[str, Any],
    ) -> dict[str, Any]:
        return self._request(
            "PUT",
            f"/v1/pdf/projects/{project_id}",
            json=update,
        ).json()

    def list_pdf_revisions(self, project_id: str) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            f"/v1/pdf/projects/{project_id}/revisions",
        ).json()

    def restore_pdf_revision(
        self,
        project_id: str,
        version: int,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        payload = {"expectedVersion": expected_version} if expected_version else {}
        return self._request(
            "POST",
            f"/v1/pdf/projects/{project_id}/revisions/{version}/restore",
            json=payload,
        ).json()

    def list_pdf_assets(self, project_id: str) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            f"/v1/pdf/projects/{project_id}/assets",
        ).json()

    def upload_pdf_asset(
        self,
        project_id: str,
        path: str | Path,
        media_type: str = "application/octet-stream",
    ) -> dict[str, Any]:
        file_path = Path(path)
        with file_path.open("rb") as handle:
            return self._request(
                "POST",
                f"/v1/pdf/projects/{project_id}/assets",
                files={"file": (file_path.name, handle, media_type)},
            ).json()

    def list_pdf_jobs(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/v1/pdf/projects/{project_id}/jobs").json()

    def list_pdf_audit(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/v1/pdf/projects/{project_id}/audit").json()

    def list_pdf_access(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/v1/pdf/projects/{project_id}/access").json()

    def grant_pdf_access(
        self,
        project_id: str,
        principal_type: str,
        principal_id: str,
        role: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/pdf/projects/{project_id}/access",
            json={
                "principalType": principal_type,
                "principalId": principal_id,
                "role": role,
            },
        ).json()

    def revoke_pdf_access(self, project_id: str, grant_id: str) -> None:
        self._request("DELETE", f"/v1/pdf/projects/{project_id}/access/{grant_id}")

    def list_pdf_webhooks(self, project_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/v1/pdf/projects/{project_id}/webhooks").json()

    def create_pdf_webhook(
        self,
        project_id: str,
        endpoint: str,
        events: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/pdf/projects/{project_id}/webhooks",
            json={"endpoint": endpoint, "events": events or ["pdf.*"]},
        ).json()

    def delete_pdf_webhook(self, project_id: str, webhook_id: str) -> None:
        self._request(
            "DELETE",
            f"/v1/pdf/projects/{project_id}/webhooks/{webhook_id}",
        )

    def list_pdf_webhook_deliveries(self, project_id: str) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            f"/v1/pdf/projects/{project_id}/webhook-deliveries",
        ).json()

    def export_pdf(self, project_id: str, profile: str = "standard") -> bytes:
        return self._request(
            "POST",
            f"/v1/pdf/projects/{project_id}/export",
            json={"profile": profile},
        ).content
