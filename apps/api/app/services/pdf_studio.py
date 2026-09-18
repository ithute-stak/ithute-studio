from __future__ import annotations

import base64
import binascii
import io
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.studio import StudioPdfProject
from app.schemas.pdf_studio import PdfEditLayer, PdfProjectUpdate

JsonObject = dict[str, Any]


class PdfStudioError(ValueError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _project_payload(row: StudioPdfProject) -> JsonObject:
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
        "createdAt": _iso(row.created_at),
        "updatedAt": _iso(row.updated_at),
    }


def _project_dir(project_id: uuid.UUID) -> Path:
    root = Path(get_settings().storage_root).expanduser().resolve()
    path = root / "pdf-projects" / str(project_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _inspect_pdf(path: Path) -> tuple[int, list[JsonObject]]:
    try:
        pdf = pdfium.PdfDocument(str(path))
    except Exception as exc:
        raise PdfStudioError("The uploaded file is not a readable PDF") from exc

    metadata: list[JsonObject] = []
    try:
        page_count = len(pdf)
        if page_count < 1:
            raise PdfStudioError("The PDF does not contain any pages")
        for index in range(page_count):
            page = pdf[index]
            try:
                width, height = page.get_size()
                metadata.append(
                    {
                        "index": index,
                        "width": round(float(width), 3),
                        "height": round(float(height), 3),
                    }
                )
            finally:
                page.close()
        return page_count, metadata
    finally:
        pdf.close()


async def list_pdf_projects(session: AsyncSession) -> list[JsonObject]:
    rows = (
        await session.execute(
            select(StudioPdfProject).order_by(StudioPdfProject.updated_at.desc())
        )
    ).scalars().all()
    return [_project_payload(row) for row in rows]


async def get_pdf_project(
    session: AsyncSession,
    project_id: str,
) -> StudioPdfProject | None:
    try:
        identifier = uuid.UUID(project_id)
    except ValueError:
        return None
    return await session.get(StudioPdfProject, identifier)


async def create_pdf_project(
    session: AsyncSession,
    *,
    filename: str,
    content: bytes,
    name: str | None = None,
) -> JsonObject:
    settings = get_settings()
    max_bytes = settings.max_pdf_upload_mb * 1024 * 1024
    if not content or len(content) > max_bytes:
        raise PdfStudioError(
            f"PDF must be between 1 byte and {settings.max_pdf_upload_mb} MB"
        )
    if not content.startswith(b"%PDF-"):
        raise PdfStudioError("Only PDF files are accepted")

    identifier = uuid.uuid4()
    project_dir = _project_dir(identifier)
    source = project_dir / "source.pdf"
    source.write_bytes(content)

    try:
        page_count, page_metadata = _inspect_pdf(source)
    except Exception:
        shutil.rmtree(project_dir, ignore_errors=True)
        raise

    now = _now()
    safe_name = (name or Path(filename).stem or "Untitled PDF").strip()[:240]
    row = StudioPdfProject(
        id=identifier,
        name=safe_name or "Untitled PDF",
        original_filename=(Path(filename).name or "document.pdf")[:512],
        source_path=str(source),
        page_count=page_count,
        page_order=list(range(page_count)),
        page_metadata=page_metadata,
        page_rotations={},
        edits=[],
        version=1,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _project_payload(row)


def _validate_page_order(page_order: list[int], page_count: int) -> list[int]:
    if not page_order:
        raise PdfStudioError("A PDF project must contain at least one page")
    if any(index < 0 or index >= page_count for index in page_order):
        raise PdfStudioError("Page order contains an invalid source page index")
    return page_order


async def update_pdf_project(
    session: AsyncSession,
    project_id: str,
    update: PdfProjectUpdate,
) -> JsonObject | None:
    try:
        identifier = uuid.UUID(project_id)
    except ValueError:
        return None

    row = (
        await session.execute(
            select(StudioPdfProject)
            .where(StudioPdfProject.id == identifier)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    if update.expected_version is not None and row.version != update.expected_version:
        raise PdfStudioError("version_conflict")

    if update.name is not None:
        row.name = update.name.strip() or row.name
    if update.page_order is not None:
        row.page_order = _validate_page_order(update.page_order, row.page_count)
    if update.page_rotations is not None:
        row.page_rotations = {
            str(key): int(value) for key, value in update.page_rotations.items()
        }
    if update.edits is not None:
        row.edits = [item.model_dump(by_alias=True) for item in update.edits]

    row.version += 1
    row.updated_at = _now()
    await session.commit()
    await session.refresh(row)
    return _project_payload(row)


async def delete_pdf_project(session: AsyncSession, project_id: str) -> bool:
    row = await get_pdf_project(session, project_id)
    if row is None:
        return False
    source_path = Path(row.source_path)
    await session.execute(delete(StudioPdfProject).where(StudioPdfProject.id == row.id))
    await session.commit()
    shutil.rmtree(source_path.parent, ignore_errors=True)
    return True


def render_pdf_page(row: StudioPdfProject, page_index: int, scale: float = 1.25) -> bytes:
    if page_index < 0 or page_index >= row.page_count:
        raise PdfStudioError("Page not found")
    scale = max(0.35, min(float(scale), 4.0))
    pdf = pdfium.PdfDocument(row.source_path)
    try:
        page = pdf[page_index]
        try:
            bitmap = page.render(scale=scale)
            image = bitmap.to_pil()
            output = io.BytesIO()
            image.save(output, format="PNG", optimize=True)
            return output.getvalue()
        finally:
            page.close()
    finally:
        pdf.close()


def extract_pdf_text(row: StudioPdfProject, page_index: int) -> list[JsonObject]:
    if page_index < 0 or page_index >= row.page_count:
        raise PdfStudioError("Page not found")

    pdf = pdfium.PdfDocument(row.source_path)
    runs: list[JsonObject] = []
    try:
        page = pdf[page_index]
        try:
            _, page_height = page.get_size()
            text_page = page.get_textpage()
            try:
                objects = page.get_objects(
                    filter=(pdfium_c.FPDF_PAGEOBJ_TEXT,),
                    max_depth=8,
                    textpage=text_page,
                )
                for text_object in objects:
                    try:
                        text = text_object.extract().strip()
                    except Exception:
                        continue
                    if not text:
                        continue
                    left, bottom, right, top = text_object.get_bounds()
                    try:
                        font_size = float(text_object.get_font_size())
                    except Exception:
                        font_size = max(8.0, float(top - bottom))
                    try:
                        font = text_object.get_font().get_base_name()
                    except Exception:
                        font = "Helvetica"
                    runs.append(
                        {
                            "text": text,
                            "x": round(float(left), 3),
                            "y": round(float(page_height - top), 3),
                            "width": round(max(1.0, float(right - left)), 3),
                            "height": round(max(1.0, float(top - bottom)), 3),
                            "fontSize": round(max(4.0, font_size), 2),
                            "fontFamily": font or "Helvetica",
                        }
                    )
            finally:
                text_page.close()
        finally:
            page.close()
    finally:
        pdf.close()
    return runs


def _hex_color(value: str, default: str = "#111111") -> Color:
    raw = (value or default).lstrip("#")
    if len(raw) == 3:
        raw = "".join(char * 2 for char in raw)
    try:
        red, green, blue = (int(raw[index : index + 2], 16) for index in (0, 2, 4))
    except (ValueError, TypeError):
        return _hex_color(default, "#111111") if value != default else Color(0, 0, 0)
    return Color(red / 255, green / 255, blue / 255)


def _decode_data_url(value: str | None) -> bytes | None:
    if not value or not value.startswith("data:image/") or "," not in value:
        return None
    header, payload = value.split(",", 1)
    if ";base64" not in header:
        return None
    try:
        data = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        return None
    if len(data) > 15 * 1024 * 1024:
        return None
    return data


def _set_alpha(pdf_canvas: canvas.Canvas, opacity: float) -> None:
    value = max(0.0, min(float(opacity), 1.0))
    if hasattr(pdf_canvas, "setFillAlpha"):
        pdf_canvas.setFillAlpha(value)
    if hasattr(pdf_canvas, "setStrokeAlpha"):
        pdf_canvas.setStrokeAlpha(value)


def _draw_layer(
    pdf_canvas: canvas.Canvas,
    layer: PdfEditLayer,
    page_height: float,
) -> None:
    x = float(layer.x)
    width = max(0.0, float(layer.width))
    height = max(0.0, float(layer.height))
    y = page_height - float(layer.y) - height
    _set_alpha(pdf_canvas, layer.opacity)
    pdf_canvas.setLineWidth(layer.stroke_width)
    pdf_canvas.setStrokeColor(_hex_color(layer.stroke))
    pdf_canvas.setFillColor(_hex_color(layer.fill))

    if layer.type == "cover":
        pdf_canvas.setFillColor(_hex_color(layer.fill, "#ffffff"))
        pdf_canvas.rect(x, y, width, height, fill=1, stroke=0)
        return
    if layer.type == "rectangle":
        pdf_canvas.rect(x, y, width, height, fill=1, stroke=1)
        return
    if layer.type == "ellipse":
        pdf_canvas.ellipse(x, y, x + width, y + height, fill=1, stroke=1)
        return
    if layer.type == "highlight":
        pdf_canvas.setFillColor(_hex_color(layer.fill, "#fff59d"))
        _set_alpha(pdf_canvas, min(layer.opacity, 0.55))
        pdf_canvas.rect(x, y, width, height, fill=1, stroke=0)
        return
    if layer.type == "image":
        data = _decode_data_url(layer.data_url)
        if data:
            pdf_canvas.drawImage(
                ImageReader(io.BytesIO(data)),
                x,
                y,
                width=width,
                height=height,
                preserveAspectRatio=True,
                mask="auto",
            )
        return
    if layer.type != "text":
        return

    if layer.erase_original:
        pdf_canvas.saveState()
        pdf_canvas.setFillColor(_hex_color(layer.fill, "#ffffff"))
        pdf_canvas.rect(x, y, width, height, fill=1, stroke=0)
        pdf_canvas.restoreState()

    font_family = layer.font_family
    standard_fonts = {
        "Helvetica",
        "Helvetica-Bold",
        "Helvetica-Oblique",
        "Times-Roman",
        "Times-Bold",
        "Times-Italic",
        "Courier",
        "Courier-Bold",
        "Courier-Oblique",
    }
    if font_family not in standard_fonts:
        lower = font_family.lower()
        font_family = "Times-Roman" if "times" in lower or "serif" in lower else "Helvetica"
    pdf_canvas.setFillColor(_hex_color(layer.color, "#111111"))
    pdf_canvas.setFont(font_family, layer.font_size)
    text = (layer.text or "").replace("\r", "")
    baseline = y + max(0.0, height - layer.font_size) / 2
    text_object = pdf_canvas.beginText(x, baseline)
    text_object.setFont(font_family, layer.font_size)
    text_object.setFillColor(_hex_color(layer.color, "#111111"))
    for line_number, line in enumerate(text.split("\n")):
        if line_number:
            text_object.textLine("")
        text_object.textOut(line)
    pdf_canvas.drawText(text_object)


def _build_overlay(
    page_width: float,
    page_height: float,
    layers: list[PdfEditLayer],
) -> bytes:
    output = io.BytesIO()
    pdf_canvas = canvas.Canvas(output, pagesize=(page_width, page_height))
    for layer in layers:
        pdf_canvas.saveState()
        _draw_layer(pdf_canvas, layer, page_height)
        pdf_canvas.restoreState()
    pdf_canvas.showPage()
    pdf_canvas.save()
    return output.getvalue()


def export_pdf_project(row: StudioPdfProject) -> bytes:
    source = Path(row.source_path)
    if not source.exists():
        raise PdfStudioError("The source PDF is missing from backend storage")

    page_order = _validate_page_order(list(row.page_order or []), row.page_count)
    edits = [PdfEditLayer.model_validate(item) for item in (row.edits or [])]
    edits_by_page: dict[int, list[PdfEditLayer]] = {}
    for edit in edits:
        edits_by_page.setdefault(edit.page, []).append(edit)

    reader = PdfReader(str(source))
    writer = PdfWriter()
    for source_index in page_order:
        writer.add_page(reader.pages[source_index])
        output_page = writer.pages[-1]
        page_width = float(output_page.mediabox.width)
        page_height = float(output_page.mediabox.height)
        layers = edits_by_page.get(source_index, [])
        if layers:
            overlay_bytes = _build_overlay(page_width, page_height, layers)
            overlay_page = PdfReader(io.BytesIO(overlay_bytes)).pages[0]
            output_page.merge_page(overlay_page, over=True)
        rotation = int((row.page_rotations or {}).get(str(source_index), 0))
        if rotation:
            output_page.rotate(rotation)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
