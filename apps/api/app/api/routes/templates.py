from typing import Any

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import DbSession
from app.schemas.studio import ResolveTemplateRequest
from app.services import studio_store
from app.template_engine import resolve_doc_json

router = APIRouter(prefix="/v1/templates", tags=["templates"])


@router.post("/resolve")
async def resolve_template(request: ResolveTemplateRequest) -> dict[str, Any]:
    document = request.document.copy()
    for region in ("header", "body", "footer"):
        document[region] = resolve_doc_json(document.get(region), request.data)
    document["variables"] = request.data
    return document


@router.get("")
async def list_templates(session: DbSession) -> list[dict[str, Any]]:
    return await studio_store.list_templates(session)


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
