from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.schemas.studio import GenerateDocumentRequest, SaveDocumentRequest
from app.services import studio_store
from app.template_engine import generate_document

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.post("/from-template", status_code=status.HTTP_201_CREATED)
async def create_from_template(
    request: GenerateDocumentRequest,
    session: DbSession,
) -> dict[str, Any]:
    template = request.template
    if template is None and request.template_id:
        template = await studio_store.get_template(session, request.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    template_document = (
        template.get("document")
        if isinstance(template.get("document"), dict)
        else template
    )
    source = request.source.model_dump(by_alias=True) if request.source else None
    generated = generate_document(template_document, request.data, source)
    if request.persist:
        return await studio_store.create_document(session, generated)
    return generated


@router.get("")
async def list_documents(session: DbSession) -> list[dict[str, Any]]:
    return await studio_store.list_documents(session)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: dict[str, Any],
    session: DbSession,
) -> dict[str, Any]:
    return await studio_store.create_document(session, payload)


@router.get("/{document_id}")
async def get_document(document_id: str, session: DbSession) -> dict[str, Any]:
    item = await studio_store.get_document(session, document_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return item


@router.put("/{document_id}")
async def save_document(
    document_id: str,
    request: SaveDocumentRequest,
    session: DbSession,
) -> dict[str, Any]:
    try:
        item = await studio_store.save_document(
            session,
            document_id,
            request.document,
            request.expected_version,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail="Document changed since the supplied version",
        ) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return item
