from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response

from app.api.deps import DbSession
from app.document_renderer import render_docx, render_pdf
from app.html_renderer import render_html
from app.schemas.business_ops import (
    ApprovalDecision,
    ApprovalRuleCreate,
    DeliveryCreate,
    DeliveryUpdate,
    IssueDocumentRequest,
    OrganizationCreate,
    PartyCreate,
    PaymentCreate,
    RecurringCreate,
    RelationCreate,
    SequenceCreate,
    StatusChangeRequest,
)
from app.services import business_ops

router = APIRouter(prefix="/v1/operations", tags=["document operations"])


def _error(exc: ValueError) -> HTTPException:
    mapping = {
        "organization_not_found": (404, "Organization not found"),
        "party_not_found": (404, "Customer/supplier not found"),
        "template_not_found": (404, "Template not found"),
        "document_not_found": (404, "Registered document not found"),
        "approval_not_found": (404, "Approval step not found"),
        "delivery_not_found": (404, "Delivery record not found"),
        "recurring_not_found": (404, "Recurring document not found"),
        "recurring_not_active": (409, "Recurring document is not active"),
        "invalid_status_transition": (409, "Invalid document status transition"),
        "approval_already_decided": (409, "Approval step was already decided"),
        "prior_approval_pending": (409, "A prior approval step is still pending"),
    }
    status_code, detail = mapping.get(str(exc), (400, str(exc)))
    return HTTPException(status_code=status_code, detail=detail)


@router.post("/organizations", status_code=201)
async def create_organization(
    request: OrganizationCreate, session: DbSession
) -> dict[str, Any]:
    return await business_ops.create_organization(
        session, request.model_dump(by_alias=True)
    )


@router.get("/organizations")
async def list_organizations(session: DbSession) -> list[dict[str, Any]]:
    return await business_ops.list_organizations(session)


@router.put("/organizations/{organization_id}")
async def update_organization(
    organization_id: str,
    request: OrganizationCreate,
    session: DbSession,
) -> dict[str, Any]:
    item = await business_ops.update_organization(
        session,
        organization_id,
        request.model_dump(by_alias=True),
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return item


@router.post("/parties", status_code=201)
async def create_party(request: PartyCreate, session: DbSession) -> dict[str, Any]:
    return await business_ops.create_party(session, request.model_dump(by_alias=True))


@router.get("/parties")
async def list_parties(
    session: DbSession,
    organization_id: str = Query(alias="organizationId"),
    kind: str | None = None,
) -> list[dict[str, Any]]:
    return await business_ops.list_parties(session, organization_id, kind)


@router.post("/sequences", status_code=201)
async def put_sequence(
    request: SequenceCreate, session: DbSession
) -> dict[str, Any]:
    return await business_ops.put_sequence(session, request.model_dump(by_alias=True))


@router.post("/documents/issue", status_code=201)
async def issue_document(
    request: IssueDocumentRequest, session: DbSession
) -> dict[str, Any]:
    try:
        return await business_ops.issue_document(
            session, request.model_dump(by_alias=True)
        )
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/documents")
async def list_register(
    session: DbSession,
    organization_id: str = Query(alias="organizationId"),
    status: str | None = None,
    document_type: str | None = Query(default=None, alias="documentType"),
    search: str | None = None,
) -> list[dict[str, Any]]:
    return await business_ops.list_register(
        session,
        organization_id,
        status,
        document_type,
        search,
    )


@router.get("/documents/{register_id}")
async def get_register(register_id: str, session: DbSession) -> dict[str, Any]:
    item = await business_ops.get_register(session, register_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Registered document not found")
    return item


@router.post("/documents/{register_id}/status")
async def change_status(
    register_id: str,
    request: StatusChangeRequest,
    session: DbSession,
) -> dict[str, Any]:
    try:
        item = await business_ops.change_status(
            session,
            register_id,
            request.status,
            request.actor,
            request.comment,
        )
    except ValueError as exc:
        raise _error(exc) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Registered document not found")
    return item


@router.post("/documents/{register_id}/payments", status_code=201)
async def add_payment(
    register_id: str,
    request: PaymentCreate,
    session: DbSession,
) -> dict[str, Any]:
    try:
        return await business_ops.add_payment(
            session, register_id, request.model_dump()
        )
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/relations", status_code=201)
async def add_relation(
    request: RelationCreate, session: DbSession
) -> dict[str, Any]:
    return await business_ops.add_relation(session, request.model_dump(by_alias=True))


@router.get("/documents/{register_id}/relations")
async def document_relations(
    register_id: str, session: DbSession
) -> list[dict[str, Any]]:
    return await business_ops.document_relations(session, register_id)


@router.post("/approval-rules", status_code=201)
async def create_approval_rule(
    request: ApprovalRuleCreate, session: DbSession
) -> dict[str, Any]:
    return await business_ops.create_approval_rule(
        session, request.model_dump(by_alias=True)
    )


@router.get("/documents/{register_id}/approvals")
async def list_approvals(
    register_id: str, session: DbSession
) -> list[dict[str, Any]]:
    return await business_ops.list_approvals(session, register_id)


@router.post("/approvals/{approval_id}/decision")
async def decide_approval(
    approval_id: str,
    request: ApprovalDecision,
    session: DbSession,
) -> dict[str, Any]:
    try:
        return await business_ops.decide_approval(
            session,
            approval_id,
            request.model_dump(),
        )
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/recurring", status_code=201)
async def create_recurring(
    request: RecurringCreate, session: DbSession
) -> dict[str, Any]:
    return await business_ops.create_recurring(
        session, request.model_dump(by_alias=True, mode="json")
    )


@router.get("/recurring/due")
async def due_recurring(
    session: DbSession,
    organization_id: str = Query(alias="organizationId"),
) -> list[dict[str, Any]]:
    return await business_ops.due_recurring(session, organization_id)


@router.post("/recurring/{recurring_id}/run")
async def run_recurring(
    recurring_id: str, session: DbSession
) -> dict[str, Any]:
    try:
        return await business_ops.run_recurring(session, recurring_id)
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/documents/{register_id}/deliveries", status_code=201)
async def queue_delivery(
    register_id: str,
    request: DeliveryCreate,
    session: DbSession,
) -> dict[str, Any]:
    return await business_ops.queue_delivery(
        session, register_id, request.model_dump()
    )


@router.put("/deliveries/{delivery_id}")
async def update_delivery(
    delivery_id: str,
    request: DeliveryUpdate,
    session: DbSession,
) -> dict[str, Any]:
    try:
        return await business_ops.update_delivery(
            session,
            delivery_id,
            request.model_dump(by_alias=True),
        )
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/verify/{code}")
async def verify_document(code: str, session: DbSession) -> dict[str, Any]:
    item = await business_ops.verify_document(session, code)
    if item is None:
        raise HTTPException(status_code=404, detail="Document verification failed")
    return item


@router.get("/dashboard/{organization_id}")
async def dashboard(organization_id: str, session: DbSession) -> dict[str, Any]:
    return await business_ops.dashboard(session, organization_id)


@router.get("/documents/{register_id}/render")
async def render_registered_document(
    register_id: str,
    session: DbSession,
    format: str = Query(default="pdf", pattern="^(pdf|docx|html)$"),
) -> Response:
    result = await business_ops.get_official_document(session, register_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Registered document not found")
    register, document = result
    payload = dict(document.payload or {})
    stem = re_safe_filename(register.document_number)
    headers = {
        "X-Ithute-Verification-Code": register.verification_code,
        "Content-Disposition": f'attachment; filename="{stem}.{format}"',
    }
    if format == "pdf":
        return Response(render_pdf(payload), media_type="application/pdf", headers=headers)
    if format == "docx":
        return Response(
            render_docx(payload),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers,
        )
    return Response(render_html(payload), media_type="text/html", headers=headers)


def re_safe_filename(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in "-_." else "-" for char in value)
    return safe.strip("-.") or "document"
