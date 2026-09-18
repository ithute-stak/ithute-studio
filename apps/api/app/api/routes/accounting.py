from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Response

from app.api.deps import DbSession
from app.document_renderer import render_docx, render_pdf
from app.html_renderer import render_html
from app.schemas.studio import AccountingPreviewRequest, AccountingRenderRequest
from app.services import studio_store
from app.services.accounting_engine import (
    accounting_form_schema,
    prepare_accounting_data,
)
from app.services.accounting_templates import get_accounting_template
from app.services.business_document_templates import get_business_document_template
from app.template_engine import generate_document

router = APIRouter(prefix="/v1/accounting", tags=["accounting"])


def _template(template_id: str) -> dict[str, Any]:
    template = get_accounting_template(template_id) or get_business_document_template(
        template_id
    )
    if template is None:
        raise HTTPException(status_code=404, detail="Accounting/business template not found")
    return template


def _prepared(template: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    prepared = prepare_accounting_data(template, data)
    verification = prepared.setdefault("verification", {})
    if isinstance(verification, dict) and verification.get("code") in {None, "", "DRAFT"}:
        design = template.get("document", {}).get("design", {})
        prefix = str(
            template.get("documentPrefix")
            or (design.get("documentPrefix") if isinstance(design, dict) else "")
            or "DOC"
        )
        verification["code"] = f"ITH-{prefix}-{uuid.uuid4().hex[:10].upper()}"
    return prepared


def _filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-.")
    return cleaned or "accounting-document"


@router.get("/templates/{template_id}/form")
async def accounting_form(template_id: str) -> dict[str, Any]:
    template = _template(template_id)
    return accounting_form_schema(template)


@router.post("/preview")
async def preview_accounting_document(request: AccountingPreviewRequest) -> dict[str, Any]:
    template = _template(request.template_id)
    data = _prepared(template, request.data)
    document = generate_document(
        template["document"],
        data,
        {"provider": "ithute-studio", "entityType": "accounting-preview"},
    )
    return {
        "template": {
            "id": template["id"],
            "name": template["name"],
            "documentType": template["documentType"],
            "styleName": template["styleName"],
        },
        "form": accounting_form_schema(template),
        "data": data,
        "document": document,
    }


@router.post("/render")
async def render_accounting_document(
    request: AccountingRenderRequest,
    session: DbSession,
) -> Response:
    template = _template(request.template_id)
    data = _prepared(template, request.data)
    document = generate_document(
        template["document"],
        data,
        {
            "provider": "ithute-studio",
            "entityType": "accounting-document",
            "entityId": str(data.get("document", {}).get("number") or ""),
        },
    )
    persisted_id: str | None = None
    if request.persist:
        persisted = await studio_store.create_document(session, document)
        persisted_id = str(persisted["id"])
        document = persisted

    number = str(data.get("document", {}).get("number") or template["documentTypeLabel"])
    stem = _filename(number)
    headers = {"X-Ithute-Verification-Code": str(data["verification"]["code"])}
    if persisted_id:
        headers["X-Ithute-Document-Id"] = persisted_id

    if request.format == "pdf":
        headers["Content-Disposition"] = f'attachment; filename="{stem}.pdf"'
        return Response(render_pdf(document), media_type="application/pdf", headers=headers)
    if request.format == "docx":
        headers["Content-Disposition"] = f'attachment; filename="{stem}.docx"'
        return Response(
            render_docx(document),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers,
        )
    headers["Content-Disposition"] = f'inline; filename="{stem}.html"'
    return Response(render_html(document), media_type="text/html", headers=headers)
