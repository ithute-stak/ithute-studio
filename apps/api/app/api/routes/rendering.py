from fastapi import APIRouter, HTTPException, Response

from app.document_renderer import render_docx, render_pdf
from app.html_renderer import render_html
from app.schemas.studio import RenderRequest

router = APIRouter(prefix="/v1", tags=["rendering"])


@router.post("/render")
async def render_document(request: RenderRequest) -> Response:
    title = str(
        (request.document.get("properties") or {}).get("title") or "document"
    ).replace("/", "-")

    if request.format == "html":
        return Response(
            render_html(request.document),
            media_type="text/html",
            headers={"Content-Disposition": f'inline; filename="{title}.html"'},
        )
    if request.format == "pdf":
        return Response(
            render_pdf(request.document),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{title}.pdf"'},
        )
    if request.format == "docx":
        return Response(
            render_docx(request.document),
            media_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
            headers={"Content-Disposition": f'attachment; filename="{title}.docx"'},
        )
    raise HTTPException(status_code=400, detail="Unsupported format")
