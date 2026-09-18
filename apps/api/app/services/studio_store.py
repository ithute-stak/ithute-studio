from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.studio import StudioDocument, StudioTemplate
from app.services.accounting_templates import (
    get_accounting_template,
    list_accounting_templates,
)
from app.services.institution_contract_templates import (
    get_institution_contract_template,
    list_institution_contract_templates,
)
from app.services.lesotho_template_packs import (
    get_lesotho_template,
    list_lesotho_templates,
)

JsonObject = dict[str, Any]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _uuid(value: object | None) -> uuid.UUID:
    if value:
        try:
            return uuid.UUID(str(value))
        except ValueError:
            pass
    return uuid.uuid4()


def _template_payload(row: StudioTemplate) -> JsonObject:
    item = dict(row.payload or {})
    item["id"] = str(row.id)
    item["name"] = row.name
    item["category"] = row.category
    item["createdAt"] = _iso(row.created_at)
    item["updatedAt"] = _iso(row.updated_at)
    return item


def _document_payload(row: StudioDocument) -> JsonObject:
    item = dict(row.payload or {})
    item["id"] = str(row.id)
    item["version"] = row.version
    item["createdAt"] = _iso(row.created_at)
    item["updatedAt"] = _iso(row.updated_at)
    return item


async def list_templates(session: AsyncSession) -> list[JsonObject]:
    rows = (
        await session.execute(
            select(StudioTemplate).order_by(StudioTemplate.updated_at.desc())
        )
    ).scalars().all()
    custom = [_template_payload(row) for row in rows]
    custom_ids = {item["id"] for item in custom}
    built_ins = [
        item
        for item in (
            list_accounting_templates()
            + list_lesotho_templates()
            + list_institution_contract_templates()
        )
        if item["id"] not in custom_ids
    ]
    return custom + built_ins


async def get_template(
    session: AsyncSession,
    template_id: str,
) -> JsonObject | None:
    try:
        identifier = uuid.UUID(template_id)
    except ValueError:
        return None
    row = await session.get(StudioTemplate, identifier)
    if row:
        return _template_payload(row)
    builtin_id = str(identifier)
    return (
        get_accounting_template(builtin_id)
        or get_lesotho_template(builtin_id)
        or get_institution_contract_template(builtin_id)
    )


async def put_template(
    session: AsyncSession,
    payload: JsonObject,
    template_id: str | None = None,
) -> JsonObject:
    identifier = _uuid(template_id or payload.get("id"))
    row = await session.get(StudioTemplate, identifier)
    now = _now()

    if row is None:
        row = StudioTemplate(
            id=identifier,
            name=str(payload.get("name") or "Untitled template"),
            category=str(payload.get("category") or "custom"),
            payload={},
            created_at=now,
            updated_at=now,
        )
        session.add(row)
    else:
        row.name = str(payload.get("name") or row.name or "Untitled template")
        row.category = str(payload.get("category") or row.category or "custom")
        row.updated_at = now

    item = dict(payload)
    item["id"] = str(identifier)
    item["name"] = row.name
    item["category"] = row.category
    item["createdAt"] = _iso(row.created_at)
    item["updatedAt"] = _iso(row.updated_at)
    row.payload = item

    await session.commit()
    await session.refresh(row)
    return _template_payload(row)


async def delete_template(session: AsyncSession, template_id: str) -> bool:
    try:
        identifier = uuid.UUID(template_id)
    except ValueError:
        return False
    result = await session.execute(
        delete(StudioTemplate).where(StudioTemplate.id == identifier)
    )
    await session.commit()
    return bool(result.rowcount)


async def list_documents(session: AsyncSession) -> list[JsonObject]:
    rows = (
        await session.execute(
            select(StudioDocument).order_by(StudioDocument.updated_at.desc())
        )
    ).scalars().all()
    return [_document_payload(row) for row in rows]


async def get_document(
    session: AsyncSession,
    document_id: str,
) -> JsonObject | None:
    try:
        identifier = uuid.UUID(document_id)
    except ValueError:
        return None
    row = await session.get(StudioDocument, identifier)
    return _document_payload(row) if row else None


async def create_document(
    session: AsyncSession,
    payload: JsonObject,
) -> JsonObject:
    identifier = _uuid(payload.get("id"))
    now = _now()
    item = dict(payload)
    item["id"] = str(identifier)
    item.setdefault("schemaVersion", 1)
    item["version"] = int(item.get("version") or 1)
    item["createdAt"] = str(item.get("createdAt") or _iso(now))
    item["updatedAt"] = _iso(now)
    title = str((item.get("properties") or {}).get("title") or "Untitled document")

    row = StudioDocument(
        id=identifier,
        title=title,
        version=item["version"],
        payload=item,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _document_payload(row)


async def save_document(
    session: AsyncSession,
    document_id: str,
    payload: JsonObject,
    expected_version: int | None = None,
) -> JsonObject | None:
    try:
        identifier = uuid.UUID(document_id)
    except ValueError:
        return None

    row = (
        await session.execute(
            select(StudioDocument)
            .where(StudioDocument.id == identifier)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    if expected_version is not None and row.version != expected_version:
        raise ValueError("version_conflict")

    now = _now()
    next_version = row.version + 1
    item = dict(payload)
    item["id"] = str(row.id)
    item["createdAt"] = _iso(row.created_at)
    item["updatedAt"] = _iso(now)
    item["version"] = next_version

    row.title = str(
        (item.get("properties") or {}).get("title") or "Untitled document"
    )
    row.version = next_version
    row.payload = item
    row.updated_at = now

    await session.commit()
    await session.refresh(row)
    return _document_payload(row)
