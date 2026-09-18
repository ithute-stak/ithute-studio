from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.pdf_platform import (
    StudioPdfAccessGrant,
    StudioPdfWebhookDelivery,
    StudioPdfWebhookSubscription,
)
from app.models.studio import StudioPdfAuditEvent
from app.schemas.pdf_collaboration import PdfAccessGrantCreate, PdfWebhookCreate

JsonObject = dict[str, Any]


def _uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


def _matches(events: list[str], action: str) -> bool:
    return action in events or "pdf.*" in events


async def list_access_grants(
    session: AsyncSession, project_id: uuid.UUID
) -> list[JsonObject]:
    rows = (
        await session.execute(
            select(StudioPdfAccessGrant)
            .where(StudioPdfAccessGrant.project_id == project_id)
            .order_by(StudioPdfAccessGrant.created_at.asc())
        )
    ).scalars().all()
    return [
        {
            "id": str(row.id),
            "projectId": str(row.project_id),
            "principalType": row.principal_type,
            "principalId": row.principal_id,
            "role": row.role,
            "createdAt": row.created_at.isoformat(),
        }
        for row in rows
    ]


async def put_access_grant(
    session: AsyncSession,
    project_id: uuid.UUID,
    request: PdfAccessGrantCreate,
) -> JsonObject:
    row = (
        await session.execute(
            select(StudioPdfAccessGrant).where(
                StudioPdfAccessGrant.project_id == project_id,
                StudioPdfAccessGrant.principal_type == request.principal_type,
                StudioPdfAccessGrant.principal_id == request.principal_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = StudioPdfAccessGrant(
            project_id=project_id,
            principal_type=request.principal_type,
            principal_id=request.principal_id,
            role=request.role,
        )
        session.add(row)
    else:
        row.role = request.role
    await session.flush()
    return {
        "id": str(row.id),
        "projectId": str(row.project_id),
        "principalType": row.principal_type,
        "principalId": row.principal_id,
        "role": row.role,
        "createdAt": row.created_at.isoformat(),
    }


async def delete_access_grant(
    session: AsyncSession, project_id: uuid.UUID, grant_id: str
) -> bool:
    identifier = _uuid(grant_id)
    if identifier is None:
        return False
    result = await session.execute(
        delete(StudioPdfAccessGrant).where(
            StudioPdfAccessGrant.id == identifier,
            StudioPdfAccessGrant.project_id == project_id,
        )
    )
    return bool(result.rowcount)


async def list_webhooks(
    session: AsyncSession, project_id: uuid.UUID
) -> list[JsonObject]:
    rows = (
        await session.execute(
            select(StudioPdfWebhookSubscription)
            .where(StudioPdfWebhookSubscription.project_id == project_id)
            .order_by(StudioPdfWebhookSubscription.created_at.asc())
        )
    ).scalars().all()
    return [
        {
            "id": str(row.id),
            "projectId": str(row.project_id),
            "endpoint": row.endpoint,
            "events": list(row.events or []),
            "isActive": row.is_active,
            "createdAt": row.created_at.isoformat(),
            "updatedAt": row.updated_at.isoformat(),
        }
        for row in rows
    ]


async def create_webhook(
    session: AsyncSession,
    project_id: uuid.UUID,
    request: PdfWebhookCreate,
) -> JsonObject:
    endpoint = str(request.endpoint)
    settings = get_settings()
    if settings.environment.lower() == "production" and not endpoint.startswith("https://"):
        raise ValueError("Production webhook endpoints must use HTTPS")
    row = StudioPdfWebhookSubscription(
        project_id=project_id,
        endpoint=endpoint,
        events=request.events,
        is_active=True,
    )
    session.add(row)
    await session.flush()
    return {
        "id": str(row.id),
        "projectId": str(row.project_id),
        "endpoint": row.endpoint,
        "events": list(row.events or []),
        "isActive": row.is_active,
        "createdAt": row.created_at.isoformat(),
        "updatedAt": row.updated_at.isoformat(),
    }


async def delete_webhook(
    session: AsyncSession, project_id: uuid.UUID, webhook_id: str
) -> bool:
    identifier = _uuid(webhook_id)
    if identifier is None:
        return False
    result = await session.execute(
        delete(StudioPdfWebhookSubscription).where(
            StudioPdfWebhookSubscription.id == identifier,
            StudioPdfWebhookSubscription.project_id == project_id,
        )
    )
    return bool(result.rowcount)


async def enqueue_webhook_deliveries(
    session: AsyncSession,
    event: StudioPdfAuditEvent,
) -> None:
    if event.project_id is None:
        return
    subscriptions = (
        await session.execute(
            select(StudioPdfWebhookSubscription).where(
                StudioPdfWebhookSubscription.project_id == event.project_id,
                StudioPdfWebhookSubscription.is_active.is_(True),
            )
        )
    ).scalars().all()
    payload = {
        "id": str(event.id),
        "event": event.action,
        "projectId": str(event.project_id),
        "actor": event.actor,
        "data": dict(event.details or {}),
        "createdAt": event.created_at.isoformat(),
    }
    for subscription in subscriptions:
        if not _matches(list(subscription.events or []), event.action):
            continue
        session.add(
            StudioPdfWebhookDelivery(
                subscription_id=subscription.id,
                project_id=event.project_id,
                event_name=event.action,
                payload=payload,
                status="pending",
                attempt_count=0,
            )
        )


async def list_webhook_deliveries(
    session: AsyncSession, project_id: uuid.UUID
) -> list[JsonObject]:
    rows = (
        await session.execute(
            select(StudioPdfWebhookDelivery)
            .where(StudioPdfWebhookDelivery.project_id == project_id)
            .order_by(StudioPdfWebhookDelivery.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": str(row.id),
            "subscriptionId": str(row.subscription_id),
            "projectId": str(row.project_id),
            "event": row.event_name,
            "payload": dict(row.payload or {}),
            "status": row.status,
            "attemptCount": row.attempt_count,
            "lastError": row.last_error,
            "createdAt": row.created_at.isoformat(),
            "updatedAt": row.updated_at.isoformat(),
        }
        for row in rows
    ]
