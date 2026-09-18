from __future__ import annotations

import hashlib
import io
import uuid
from datetime import datetime, timezone
from typing import Any

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.studio import (
    StudioPdfAsset,
    StudioPdfAuditEvent,
    StudioPdfJob,
    StudioPdfProject,
    StudioPdfRevision,
)
from app.services.pdf_storage import PdfStorage

JsonObject = dict[str, Any]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def project_snapshot(row: StudioPdfProject) -> JsonObject:
    return {
        "schemaVersion": row.schema_version,
        "name": row.name,
        "status": row.status,
        "pageOrder": list(row.page_order or []),
        "pageRotations": dict(row.page_rotations or {}),
        "objects": list(row.objects or row.edits or []),
        "metadata": dict(row.document_metadata or {}),
        "defaultExportProfile": row.default_export_profile,
    }


async def create_revision(session: AsyncSession, row: StudioPdfProject) -> StudioPdfRevision:
    revision = StudioPdfRevision(
        project_id=row.id,
        version=row.version,
        snapshot=project_snapshot(row),
    )
    session.add(revision)
    return revision


async def list_revisions(session: AsyncSession, project_id: uuid.UUID) -> list[JsonObject]:
    rows = (
        await session.execute(
            select(StudioPdfRevision)
            .where(StudioPdfRevision.project_id == project_id)
            .order_by(StudioPdfRevision.version.desc())
        )
    ).scalars().all()
    return [
        {
            "id": str(item.id),
            "projectId": str(item.project_id),
            "version": item.version,
            "snapshot": dict(item.snapshot or {}),
            "createdAt": item.created_at.isoformat(),
        }
        for item in rows
    ]


async def get_revision(
    session: AsyncSession,
    project_id: uuid.UUID,
    version: int,
) -> StudioPdfRevision | None:
    return (
        await session.execute(
            select(StudioPdfRevision).where(
                StudioPdfRevision.project_id == project_id,
                StudioPdfRevision.version == version,
            )
        )
    ).scalar_one_or_none()


async def add_audit_event(
    session: AsyncSession,
    *,
    project_id: uuid.UUID | None,
    action: str,
    details: JsonObject | None = None,
    actor: str | None = None,
) -> StudioPdfAuditEvent:
    event = StudioPdfAuditEvent(
        project_id=project_id,
        action=action,
        actor=actor,
        details=details or {},
    )
    session.add(event)
    return event


async def list_audit_events(
    session: AsyncSession,
    project_id: uuid.UUID,
) -> list[JsonObject]:
    rows = (
        await session.execute(
            select(StudioPdfAuditEvent)
            .where(StudioPdfAuditEvent.project_id == project_id)
            .order_by(StudioPdfAuditEvent.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": str(item.id),
            "projectId": str(item.project_id) if item.project_id else None,
            "action": item.action,
            "actor": item.actor,
            "details": dict(item.details or {}),
            "createdAt": item.created_at.isoformat(),
        }
        for item in rows
    ]


async def create_job(
    session: AsyncSession,
    *,
    project_id: uuid.UUID | None,
    kind: str,
    status: str = "queued",
    progress: int = 0,
    payload: JsonObject | None = None,
    result: JsonObject | None = None,
    error: str | None = None,
) -> StudioPdfJob:
    now = now_utc()
    job = StudioPdfJob(
        project_id=project_id,
        kind=kind,
        status=status,
        progress=max(0, min(progress, 100)),
        payload=payload or {},
        result=result or {},
        error=error,
        started_at=now if status in {"running", "completed", "failed"} else None,
        completed_at=now if status in {"completed", "failed"} else None,
    )
    session.add(job)
    return job


async def list_jobs(session: AsyncSession, project_id: uuid.UUID) -> list[JsonObject]:
    rows = (
        await session.execute(
            select(StudioPdfJob)
            .where(StudioPdfJob.project_id == project_id)
            .order_by(StudioPdfJob.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": str(item.id),
            "projectId": str(item.project_id) if item.project_id else None,
            "kind": item.kind,
            "status": item.status,
            "progress": item.progress,
            "payload": dict(item.payload or {}),
            "result": dict(item.result or {}),
            "error": item.error,
            "createdAt": item.created_at.isoformat(),
            "startedAt": item.started_at.isoformat() if item.started_at else None,
            "completedAt": item.completed_at.isoformat() if item.completed_at else None,
        }
        for item in rows
    ]


def inspect_pdf_security(content: bytes) -> JsonObject:
    try:
        reader = PdfReader(io.BytesIO(content), strict=False)
    except Exception:
        return {
            "encrypted": False,
            "hasJavaScript": False,
            "hasEmbeddedFiles": False,
            "hasForms": False,
            "inspection": "unavailable",
        }

    encrypted = bool(reader.is_encrypted)
    if encrypted:
        return {
            "encrypted": True,
            "hasJavaScript": False,
            "hasEmbeddedFiles": False,
            "hasForms": False,
            "inspection": "encrypted",
        }

    root = reader.trailer.get("/Root", {})
    names = root.get("/Names", {}) if hasattr(root, "get") else {}
    return {
        "encrypted": False,
        "hasJavaScript": bool(
            (names.get("/JavaScript") if hasattr(names, "get") else None)
            or (root.get("/OpenAction") if hasattr(root, "get") else None)
        ),
        "hasEmbeddedFiles": bool(
            names.get("/EmbeddedFiles") if hasattr(names, "get") else None
        ),
        "hasForms": bool(root.get("/AcroForm") if hasattr(root, "get") else None),
        "inspection": "complete",
    }


async def create_asset(
    session: AsyncSession,
    storage: PdfStorage,
    *,
    project_id: uuid.UUID,
    name: str,
    media_type: str,
    content: bytes,
) -> StudioPdfAsset:
    identifier = uuid.uuid4()
    safe_name = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1] or "asset"
    key = f"pdf-projects/{project_id}/assets/{identifier}/{safe_name}"
    storage.put_bytes(key, content)
    asset = StudioPdfAsset(
        id=identifier,
        project_id=project_id,
        name=safe_name[:512],
        media_type=(media_type or "application/octet-stream")[:160],
        storage_key=key,
        sha256=sha256_bytes(content),
        size=len(content),
        asset_metadata={},
    )
    session.add(asset)
    return asset


async def list_assets(session: AsyncSession, project_id: uuid.UUID) -> list[JsonObject]:
    rows = (
        await session.execute(
            select(StudioPdfAsset)
            .where(StudioPdfAsset.project_id == project_id)
            .order_by(StudioPdfAsset.created_at.desc())
        )
    ).scalars().all()
    return [asset_payload(item) for item in rows]


def asset_payload(asset: StudioPdfAsset) -> JsonObject:
    return {
        "id": str(asset.id),
        "projectId": str(asset.project_id),
        "name": asset.name,
        "mediaType": asset.media_type,
        "sha256": asset.sha256,
        "size": asset.size,
        "metadata": dict(asset.asset_metadata or {}),
        "createdAt": asset.created_at.isoformat(),
    }
