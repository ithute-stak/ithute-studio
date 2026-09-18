from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.api.deps import DbSession
from app.schemas.pdf_collaboration import PdfAccessGrantCreate, PdfWebhookCreate
from app.services.pdf_collaboration import (
    create_webhook,
    delete_access_grant,
    delete_webhook,
    list_access_grants,
    list_webhook_deliveries,
    list_webhooks,
    put_access_grant,
)
from app.services.pdf_foundation import add_audit_event
from app.services.pdf_studio import get_pdf_project

router = APIRouter(prefix="/v1/pdf/projects/{project_id}", tags=["PDF Studio Access"])


async def _project(project_id: str, session: DbSession):
    row = await get_pdf_project(session, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="PDF project not found")
    return row


@router.get("/access")
async def access_grants(project_id: str, session: DbSession):
    row = await _project(project_id, session)
    return await list_access_grants(session, row.id)


@router.post("/access", status_code=201)
async def save_access_grant(
    project_id: str,
    request: PdfAccessGrantCreate,
    session: DbSession,
):
    row = await _project(project_id, session)
    grant = await put_access_grant(session, row.id, request)
    await add_audit_event(
        session,
        project_id=row.id,
        action="pdf.access.updated",
        details={
            "principalType": request.principal_type,
            "principalId": request.principal_id,
            "role": request.role,
        },
    )
    await session.commit()
    return grant


@router.delete("/access/{grant_id}", status_code=204)
async def remove_access_grant(project_id: str, grant_id: str, session: DbSession):
    row = await _project(project_id, session)
    if not await delete_access_grant(session, row.id, grant_id):
        raise HTTPException(status_code=404, detail="PDF access grant not found")
    await add_audit_event(
        session,
        project_id=row.id,
        action="pdf.access.deleted",
        details={"grantId": grant_id},
    )
    await session.commit()
    return Response(status_code=204)


@router.get("/webhooks")
async def webhooks(project_id: str, session: DbSession):
    row = await _project(project_id, session)
    return await list_webhooks(session, row.id)


@router.post("/webhooks", status_code=201)
async def add_webhook(project_id: str, request: PdfWebhookCreate, session: DbSession):
    row = await _project(project_id, session)
    try:
        webhook = await create_webhook(session, row.id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await add_audit_event(
        session,
        project_id=row.id,
        action="pdf.webhook.created",
        details={"webhookId": webhook["id"], "events": webhook["events"]},
    )
    await session.commit()
    return webhook


@router.delete("/webhooks/{webhook_id}", status_code=204)
async def remove_webhook(project_id: str, webhook_id: str, session: DbSession):
    row = await _project(project_id, session)
    if not await delete_webhook(session, row.id, webhook_id):
        raise HTTPException(status_code=404, detail="PDF webhook not found")
    await add_audit_event(
        session,
        project_id=row.id,
        action="pdf.webhook.deleted",
        details={"webhookId": webhook_id},
    )
    await session.commit()
    return Response(status_code=204)


@router.get("/webhook-deliveries")
async def webhook_deliveries(project_id: str, session: DbSession):
    row = await _project(project_id, session)
    return await list_webhook_deliveries(session, row.id)
