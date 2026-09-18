from typing import Any

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import DbSession
from app.schemas.studio import ResolveTemplateRequest
from app.services import studio_store
from app.services.accounting_templates import accounting_catalog_metadata
from app.template_engine import resolve_doc_json

router = APIRouter(prefix="/v1/templates", tags=["templates"])


@router.post("/resolve")
async def resolve_template(request: ResolveTemplateRequest) -> dict[str, Any]:
    document = request.document.copy()
    for region in ("header", "body", "footer"):
        document[region] = resolve_doc_json(document.get(region), request.data)
    document["variables"] = request.data
    return document


@router.get("/catalog/accounting")
async def accounting_catalog() -> dict[str, Any]:
    return accounting_catalog_metadata()


@router.get("")
async def list_templates(
    session: DbSession,
    category: str | None = None,
    document_type: str | None = None,
    style: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    items = await studio_store.list_templates(session)
    if category:
        items = [item for item in items if str(item.get("category")) == category]
    if document_type:
        items = [item for item in items if str(item.get("documentType")) == document_type]
    if style:
        items = [item for item in items if str(item.get("stylePreset")) == style]
    if search:
        needle = search.casefold()
        items = [
            item
            for item in items
            if needle
            in " ".join(
                [
                    str(item.get("name") or ""),
                    str(item.get("description") or ""),
                    " ".join(str(tag) for tag in item.get("tags") or []),
                ]
            ).casefold()
        ]
    return items


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: dict[str, Any],
    session: DbSession,
) -> dict[str, Any]:
    return await studio_store.put_template(session, payload)


@router.get("/{template_id}")
async def get_template(template_id: str, session: DbSession) -> dict[str, Any]:
    item = await studio_store.get_template(session, template_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return item


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    payload: dict[str, Any],
    session: DbSession,
) -> dict[str, Any]:
    return await studio_store.put_template(session, payload, template_id)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: str, session: DbSession) -> Response:
    deleted = await studio_store.delete_template(session, template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
