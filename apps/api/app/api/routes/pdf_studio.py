from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.deps import DbSession
from app.schemas.pdf_studio import PdfProjectUpdate
from app.services.pdf_studio import (
    PdfStudioError,
    create_pdf_project,
    delete_pdf_project,
    export_pdf_project,
    extract_pdf_text,
    get_pdf_project,
    list_pdf_projects,
    render_pdf_page,
    update_pdf_project,
)

router = APIRouter(prefix="/v1/pdf", tags=["PDF Studio"])


def _project_payload(row) -> dict:
    return {
        "id": str(row.id),
        "name": row.name,
        "originalFilename": row.original_filename,
        "pageCount": row.page_count,
        "pageOrder": list(row.page_order or []),
        "pageMetadata": list(row.page_metadata or []),
        "pageRotations": dict(row.page_rotations or {}),
        "edits": list(row.edits or []),
        "version": row.version,
        "createdAt": row.created_at.isoformat(),
        "updatedAt": row.updated_at.isoformat(),
    }


@router.get("/projects")
async def list_projects(session: DbSession):
    return await list_pdf_projects(session)


@router.post("/projects", status_code=201)
async def upload_project(
    session: DbSession,
    file: Annotated[UploadFile, File(description="PDF to edit")],
    name: Annotated[str | None, Form()] = None,
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
        )
    except PdfStudioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()


@router.get("/projects/{project_id}")
async def get_project(project_id: str, session: DbSession):
    row = await get_pdf_project(session, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="PDF project not found")
    return _project_payload(row)


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
    row = await get_pdf_project(session, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="PDF project not found")
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
    row = await get_pdf_project(session, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="PDF project not found")
    try:
        return {"items": extract_pdf_text(row, page_index)}
    except PdfStudioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/source")
async def download_source(project_id: str, session: DbSession):
    row = await get_pdf_project(session, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="PDF project not found")
    path = Path(row.source_path)
    if not path.exists():
        raise HTTPException(status_code=410, detail="Source PDF is unavailable")
    safe_name = row.original_filename.replace('"', "")
    return Response(
        content=path.read_bytes(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.post("/projects/{project_id}/export")
async def export_project(project_id: str, session: DbSession):
    row = await get_pdf_project(session, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="PDF project not found")
    try:
        content = export_pdf_project(row)
    except PdfStudioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    filename = f"{row.name.strip() or 'edited-document'}.pdf".replace('"', "")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
