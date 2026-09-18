from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.deps import DbSession
from app.schemas.pdf_studio import (
    PdfExportRequest,
    PdfProjectUpdate,
    PdfRevisionRestoreRequest,
)
from app.services.pdf_storage import StorageError, get_pdf_storage
from app.services.pdf_studio import (
    PdfStudioError,
    add_project_asset,
    create_pdf_project,
    delete_pdf_project,
    delete_project_asset,
    export_pdf_project,
    extract_pdf_text,
    get_pdf_project,
    get_project_asset,
    list_pdf_projects,
    page_object_index,
    project_assets,
    project_audit,
    project_jobs,
    project_revisions,
    render_pdf_page,
    restore_pdf_revision,
    source_pdf_bytes,
    update_pdf_project,
)

router = APIRouter(prefix="/v1/pdf", tags=["PDF Studio"])


def _project_payload(row) -> dict:
    objects = list(row.objects or row.edits or [])
    return {
        "id": str(row.id),
        "workspaceId": str(row.workspace_id) if row.workspace_id else None,
        "schemaVersion": row.schema_version,
        "name": row.name,
        "status": row.status,
        "originalFilename": row.original_filename,
        "sourceSha256": row.source_sha256,
        "sourceSize": row.source_size,
        "pageCount": row.page_count,
        "pageOrder": list(row.page_order or []),
        "pageMetadata": list(row.page_metadata or []),
        "pageRotations": dict(row.page_rotations or {}),
        "objects": objects,
        "edits": objects,
        "objectIndex": list(row.object_index or []),
        "fontCatalog": list(row.font_catalog or []),
        "metadata": dict(row.document_metadata or {}),
        "security": dict(row.security or {}),
        "importState": dict(row.import_state or {}),
        "defaultExportProfile": row.default_export_profile,
        "version": row.version,
        "createdAt": row.created_at.isoformat(),
        "updatedAt": row.updated_at.isoformat(),
    }


async def _require_project(project_id: str, session: DbSession):
    row = await get_pdf_project(session, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="PDF project not found")
    return row


@router.get("/projects")
async def list_projects(session: DbSession):
    return await list_pdf_projects(session)


@router.post("/projects", status_code=201)
async def upload_project(
    session: DbSession,
    file: Annotated[UploadFile, File(description="PDF to edit")],
    name: Annotated[str | None, Form()] = None,
    workspace_id: Annotated[str | None, Form(alias="workspaceId")] = None,
    password: Annotated[str | None, Form()] = None,
):
    filename = file.filename or "document.pdf"
    if file.content_type not in {"application/pdf", "application/octet-stream", None}:
        raise HTTPException(status_code=415, detail="Only PDF files are accepted")
    try:
        content = await file.read()
        return await create_pdf_project(
            session,
            filename=filename,
            content=content,
            name=name,
            workspace_id=workspace_id,
            password=password,
        )
    except PdfStudioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()


@router.get("/projects/{project_id}")
async def get_project(project_id: str, session: DbSession):
    return _project_payload(await _require_project(project_id, session))


@router.put("/projects/{project_id}")
async def save_project(project_id: str, update: PdfProjectUpdate, session: DbSession):
    try:
        result = await update_pdf_project(session, project_id, update)
    except PdfStudioError as exc:
        if str(exc) == "version_conflict":
            raise HTTPException(
                status_code=409,
                detail="PDF project changed since it was last loaded",
            ) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="PDF project not found")
    return result


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(project_id: str, session: DbSession):
    if not await delete_pdf_project(session, project_id):
        raise HTTPException(status_code=404, detail="PDF project not found")
    return Response(status_code=204)


@router.get("/projects/{project_id}/pages/{page_index}/preview")
async def preview_page(
    project_id: str,
    page_index: int,
    session: DbSession,
    scale: float = 1.25,
):
    row = await _require_project(project_id, session)
    try:
        content = render_pdf_page(row, page_index, scale)
    except PdfStudioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=content,
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=120"},
    )


@router.get("/projects/{project_id}/pages/{page_index}/text")
async def page_text(project_id: str, page_index: int, session: DbSession):
    row = await _require_project(project_id, session)
    try:
        return {"items": extract_pdf_text(row, page_index)}
    except PdfStudioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/pages/{page_index}/objects")
async def page_objects(project_id: str, page_index: int, session: DbSession):
    row = await _require_project(project_id, session)
    try:
        return {
            "coordinateSpace": "pdf-points-top-left",
            "items": page_object_index(row, page_index),
        }
    except PdfStudioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/revisions")
async def revisions(project_id: str, session: DbSession):
    return await project_revisions(session, await _require_project(project_id, session))


@router.post("/projects/{project_id}/revisions/{version}/restore")
async def restore_revision(
    project_id: str,
    version: int,
    session: DbSession,
    request: PdfRevisionRestoreRequest | None = Body(default=None),
):
    try:
        result = await restore_pdf_revision(
            session,
            project_id,
            version,
            request.expected_version if request else None,
        )
    except PdfStudioError as exc:
        if str(exc) == "version_conflict":
            raise HTTPException(status_code=409, detail="PDF project version conflict") from exc
        if str(exc) == "revision_not_found":
            raise HTTPException(status_code=404, detail="PDF revision not found") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="PDF project not found")
    return result


@router.get("/projects/{project_id}/audit")
async def audit(project_id: str, session: DbSession):
    return await project_audit(session, await _require_project(project_id, session))


@router.get("/projects/{project_id}/jobs")
async def jobs(project_id: str, session: DbSession):
    return await project_jobs(session, await _require_project(project_id, session))


@router.get("/projects/{project_id}/assets")
async def assets(project_id: str, session: DbSession):
    return await project_assets(session, await _require_project(project_id, session))


@router.post("/projects/{project_id}/assets", status_code=201)
async def upload_asset(
    project_id: str,
    session: DbSession,
    file: Annotated[UploadFile, File(description="PDF Studio asset")],
):
    row = await _require_project(project_id, session)
    try:
        return await add_project_asset(
            session,
            row,
            name=file.filename or "asset",
            media_type=file.content_type or "application/octet-stream",
            content=await file.read(),
        )
    except PdfStudioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()


@router.get("/projects/{project_id}/assets/{asset_id}")
async def download_asset(project_id: str, asset_id: str, session: DbSession):
    row = await _require_project(project_id, session)
    asset = await get_project_asset(session, row, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="PDF asset not found")
    try:
        content = get_pdf_storage().get_bytes(asset.storage_key)
    except StorageError as exc:
        raise HTTPException(status_code=410, detail="PDF asset is unavailable") from exc
    safe_name = asset.name.replace('"', "")
    return Response(
        content=content,
        media_type=asset.media_type,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


@router.delete("/projects/{project_id}/assets/{asset_id}", status_code=204)
async def remove_asset(project_id: str, asset_id: str, session: DbSession):
    row = await _require_project(project_id, session)
    if not await delete_project_asset(session, row, asset_id):
        raise HTTPException(status_code=404, detail="PDF asset not found")
    return Response(status_code=204)


@router.get("/projects/{project_id}/source")
async def download_source(project_id: str, session: DbSession):
    row = await _require_project(project_id, session)
    try:
        content = source_pdf_bytes(row)
    except PdfStudioError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    safe_name = row.original_filename.replace('"', "")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.post("/projects/{project_id}/export")
async def export_project(
    project_id: str,
    session: DbSession,
    request: PdfExportRequest | None = Body(default=None),
):
    row = await _require_project(project_id, session)
    try:
        content = await export_pdf_project(
            session,
            row,
            request.profile if request else None,
        )
    except PdfStudioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    filename = f"{row.name.strip() or 'edited-document'}.pdf".replace('"', "")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
