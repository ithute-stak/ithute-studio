from __future__ import annotations

import base64
import binascii
import io
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
from app.models.studio import StudioPdfAsset, StudioPdfProject
from app.schemas.pdf_studio import (
    PdfEditLayer,
    PdfExportProfile,
    PdfProjectUpdate,
)
from app.services.pdf_foundation import (
    add_audit_event,
    asset_payload,
    create_asset,
    create_job,
    create_revision,
    get_revision,
    inspect_pdf_security,
    list_assets,
    list_audit_events,
    list_jobs,
    list_revisions,
    now_utc,
    sha256_bytes,
)
from app.services.pdf_storage import StorageError, get_pdf_storage

JsonObject = dict[str, Any]
LOCKED_STATES = {"signed", "locked", "archived"}
STATUS_TRANSITIONS = {
    "draft": {"draft", "review", "archived"},
    "review": {"draft", "review", "approved", "archived"},
    "approved": {"review", "approved", "signed", "locked", "archived"},
    "signed": {"signed", "locked", "archived"},
    "locked": {"locked", "archived"},
    "archived": {"archived", "draft"},
}


class PdfStudioError(ValueError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _project_payload(row: StudioPdfProject) -> JsonObject:
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
        "createdAt": _iso(row.created_at),
        "updatedAt": _iso(row.updated_at),
    }


def _source_path(row: StudioPdfProject) -> Path:
    storage = get_pdf_storage()
    if row.source_key:
        try:
            return storage.materialize(row.source_key)
        except StorageError:
            pass
    legacy = Path(row.source_path)
    if legacy.exists():
        return legacy
    raise PdfStudioError("The source PDF is missing from backend storage")


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


def _normalize_encrypted_pdf(content: bytes, password: str | None) -> tuple[bytes, JsonObject]:
    security = inspect_pdf_security(content)
    if not security.get("encrypted"):
        return content, security
    if not password:
        raise PdfStudioError("This PDF is password protected; provide its password to import it")
    reader = PdfReader(io.BytesIO(content), strict=False)
    try:
        result = reader.decrypt(password)
    except Exception as exc:
        raise PdfStudioError("The PDF password could not be verified") from exc
    if not result:
        raise PdfStudioError("The PDF password is incorrect")
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    if reader.metadata:
        safe_metadata = {
            str(key): str(value)
            for key, value in reader.metadata.items()
            if key and value is not None
        }
        if safe_metadata:
            writer.add_metadata(safe_metadata)
    output = io.BytesIO()
    writer.write(output)
    normalized = output.getvalue()
    return normalized, {
        **security,
        "decryptedOnImport": True,
        "storedEncrypted": False,
    }


def _build_source_index(row: StudioPdfProject) -> tuple[list[JsonObject], list[JsonObject]]:
    object_index: list[JsonObject] = []
    fonts: dict[str, JsonObject] = {}
    for page_index in range(row.page_count):
        for sequence, item in enumerate(extract_pdf_text(row, page_index)):
            object_index.append(
                {
                    "id": f"source:text:{page_index}:{sequence}",
                    "page": page_index,
                    "type": "text",
                    "coordinateSpace": "pdf-points-top-left",
                    "x": item["x"],
                    "y": item["y"],
                    "width": item["width"],
                    "height": item["height"],
                    "text": item["text"],
                    "fontSize": item["fontSize"],
                    "fontFamily": item["fontFamily"],
                }
            )
            family = str(item["fontFamily"] or "Helvetica")
            fonts.setdefault(
                family,
                {
                    "family": family,
                    "source": "embedded-or-referenced",
                    "availableForExport": family
                    in {
                        "Helvetica",
                        "Helvetica-Bold",
                        "Helvetica-Oblique",
                        "Times-Roman",
                        "Times-Bold",
                        "Times-Italic",
                        "Courier",
                        "Courier-Bold",
                        "Courier-Oblique",
                    },
                },
            )
    return object_index, sorted(fonts.values(), key=lambda item: str(item["family"]).lower())


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
    workspace_id: str | None = None,
    password: str | None = None,
) -> JsonObject:
    settings = get_settings()
    max_bytes = settings.max_pdf_upload_mb * 1024 * 1024
    if not content or len(content) > max_bytes:
        raise PdfStudioError(
            f"PDF must be between 1 byte and {settings.max_pdf_upload_mb} MB"
        )
    if not content.startswith(b"%PDF-"):
        raise PdfStudioError("Only PDF files are accepted")

    upload_sha = sha256_bytes(content)
    normalized_content, security = _normalize_encrypted_pdf(content, password)
    identifier = uuid.uuid4()
    workspace_uuid: uuid.UUID | None = None
    if workspace_id:
        try:
            workspace_uuid = uuid.UUID(workspace_id)
        except ValueError as exc:
            raise PdfStudioError("workspaceId must be a UUID") from exc

    storage = get_pdf_storage()
    key = f"pdf-projects/{identifier}/source.pdf"
    storage.put_bytes(key, normalized_content)
    source = storage.materialize(key)

    try:
        page_count, page_metadata = _inspect_pdf(source)
    except Exception:
        storage.delete(key)
        raise

    now = _now()
    safe_name = (name or Path(filename).stem or "Untitled PDF").strip()[:240]
    row = StudioPdfProject(
        id=identifier,
        workspace_id=workspace_uuid,
        schema_version=1,
        name=safe_name or "Untitled PDF",
        status="draft",
        original_filename=(Path(filename).name or "document.pdf")[:512],
        storage_backend=storage.name,
        source_key=key,
        source_path=str(source),
        source_sha256=sha256_bytes(normalized_content),
        source_size=len(normalized_content),
        page_count=page_count,
        page_order=list(range(page_count)),
        page_metadata=page_metadata,
        page_rotations={},
        edits=[],
        objects=[],
        object_index=[],
        font_catalog=[],
        document_metadata={"title": safe_name or "Untitled PDF", "keywords": [], "custom": {}},
        security=security,
        import_state={
            "status": "completed",
            "uploadSha256": upload_sha,
            "coordinateSpace": "pdf-points-top-left",
            "sourceObjectIndex": "text-ready",
            "nativeImageIndex": "pending",
            "nativeVectorIndex": "pending",
            "ocr": "not-requested",
        },
        default_export_profile="standard",
        version=1,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    await session.flush()
    object_index, font_catalog = _build_source_index(row)
    row.object_index = object_index
    row.font_catalog = font_catalog
    await create_revision(session, row)
    await create_job(
        session,
        project_id=row.id,
        kind="import",
        status="completed",
        progress=100,
        result={
            "pageCount": page_count,
            "indexedObjects": len(object_index),
            "fonts": len(font_catalog),
        },
    )
    await add_audit_event(
        session,
        project_id=row.id,
        action="pdf.uploaded",
        details={
            "filename": row.original_filename,
            "pageCount": row.page_count,
            "sourceSha256": row.source_sha256,
        },
    )
    await session.commit()
    await session.refresh(row)
    return _project_payload(row)


def _validate_page_order(page_order: list[int], page_count: int) -> list[int]:
    if not page_order:
        raise PdfStudioError("A PDF project must contain at least one page")
    if any(index < 0 or index >= page_count for index in page_order):
        raise PdfStudioError("Page order contains an invalid source page index")
    return page_order


def _has_content_change(update: PdfProjectUpdate) -> bool:
    return any(
        value is not None
        for value in (
            update.name,
            update.metadata,
            update.default_export_profile,
            update.page_order,
            update.page_rotations,
            update.objects,
            update.edits,
        )
    )


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
    if row.status in LOCKED_STATES and _has_content_change(update):
        raise PdfStudioError(f"PDF project is {row.status} and cannot be edited")

    previous_status = row.status
    if update.status is not None:
        allowed = STATUS_TRANSITIONS.get(row.status, {row.status})
        if update.status not in allowed:
            raise PdfStudioError(
                f"PDF project cannot move from {row.status} to {update.status}"
            )
        row.status = update.status
    if update.name is not None:
        row.name = update.name.strip() or row.name
    if update.metadata is not None:
        row.document_metadata = update.metadata.model_dump(exclude_none=True)
    if update.default_export_profile is not None:
        row.default_export_profile = update.default_export_profile
    if update.page_order is not None:
        row.page_order = _validate_page_order(update.page_order, row.page_count)
    if update.page_rotations is not None:
        row.page_rotations = {
            str(key): int(value) for key, value in update.page_rotations.items()
        }
    incoming_objects = update.objects if update.objects is not None else update.edits
    if incoming_objects is not None:
        canonical = [item.model_dump(by_alias=True) for item in incoming_objects]
        row.objects = canonical
        row.edits = canonical

    row.version += 1
    row.updated_at = _now()
    await create_revision(session, row)
    await add_audit_event(
        session,
        project_id=row.id,
        action="pdf.updated",
        details={
            "version": row.version,
            "objectCount": len(row.objects or []),
            "status": row.status,
            "previousStatus": previous_status,
        },
    )
    await session.commit()
    await session.refresh(row)
    return _project_payload(row)


async def restore_pdf_revision(
    session: AsyncSession,
    project_id: str,
    version: int,
    expected_version: int | None = None,
) -> JsonObject | None:
    row = await get_pdf_project(session, project_id)
    if row is None:
        return None
    if expected_version is not None and row.version != expected_version:
        raise PdfStudioError("version_conflict")
    if row.status in LOCKED_STATES:
        raise PdfStudioError(f"PDF project is {row.status} and cannot restore revisions")
    revision = await get_revision(session, row.id, version)
    if revision is None:
        raise PdfStudioError("revision_not_found")
    snapshot = dict(revision.snapshot or {})
    row.name = str(snapshot.get("name") or row.name)
    row.status = "draft"
    row.page_order = _validate_page_order(
        [int(item) for item in snapshot.get("pageOrder", row.page_order)],
        row.page_count,
    )
    row.page_rotations = dict(snapshot.get("pageRotations") or {})
    row.objects = list(snapshot.get("objects") or [])
    row.edits = list(row.objects)
    row.document_metadata = dict(snapshot.get("metadata") or {})
    row.default_export_profile = str(
        snapshot.get("defaultExportProfile") or row.default_export_profile
    )
    row.version += 1
    row.updated_at = now_utc()
    await create_revision(session, row)
    await add_audit_event(
        session,
        project_id=row.id,
        action="pdf.revision.restored",
        details={"restoredVersion": version, "newVersion": row.version},
    )
    await session.commit()
    await session.refresh(row)
    return _project_payload(row)


async def delete_pdf_project(session: AsyncSession, project_id: str) -> bool:
    row = await get_pdf_project(session, project_id)
    if row is None:
        return False
    storage = get_pdf_storage()
    assets = (
        await session.execute(
            select(StudioPdfAsset).where(StudioPdfAsset.project_id == row.id)
        )
    ).scalars().all()
    for asset in assets:
        storage.delete(asset.storage_key)
    if row.source_key:
        storage.delete(row.source_key)
    await session.execute(delete(StudioPdfProject).where(StudioPdfProject.id == row.id))
    await session.commit()
    return True


def source_pdf_bytes(row: StudioPdfProject) -> bytes:
    if row.source_key:
        try:
            return get_pdf_storage().get_bytes(row.source_key)
        except StorageError:
            pass
    path = Path(row.source_path)
    if path.exists():
        return path.read_bytes()
    raise PdfStudioError("The source PDF is missing from backend storage")


def render_pdf_page(row: StudioPdfProject, page_index: int, scale: float = 1.25) -> bytes:
    if page_index < 0 or page_index >= row.page_count:
        raise PdfStudioError("Page not found")
    scale = max(0.35, min(float(scale), 4.0))
    pdf = pdfium.PdfDocument(str(_source_path(row)))
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

    pdf = pdfium.PdfDocument(str(_source_path(row)))
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


def page_object_index(row: StudioPdfProject, page_index: int) -> list[JsonObject]:
    if page_index < 0 or page_index >= row.page_count:
        raise PdfStudioError("Page not found")
    return [
        dict(item)
        for item in (row.object_index or [])
        if int(item.get("page", -1)) == page_index
    ]


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
    asset_bytes: dict[str, bytes],
) -> None:
    if not layer.visible:
        return
    x = float(layer.x)
    width = max(0.0, float(layer.width))
    height = max(0.0, float(layer.height))
    y = page_height - float(layer.y) - height
    _set_alpha(pdf_canvas, layer.opacity)
    pdf_canvas.setLineWidth(layer.stroke_width)
    pdf_canvas.setStrokeColor(_hex_color(layer.stroke))
    pdf_canvas.setFillColor(_hex_color(layer.fill))

    if layer.type in {"cover", "redaction"}:
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
        data = asset_bytes.get(layer.asset_id or "") or _decode_data_url(layer.data_url)
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
    asset_bytes: dict[str, bytes],
) -> bytes:
    output = io.BytesIO()
    pdf_canvas = canvas.Canvas(output, pagesize=(page_width, page_height))
    for layer in sorted(layers, key=lambda item: item.z_index):
        pdf_canvas.saveState()
        _draw_layer(pdf_canvas, layer, page_height, asset_bytes)
        pdf_canvas.restoreState()
    pdf_canvas.showPage()
    pdf_canvas.save()
    return output.getvalue()


def _apply_document_metadata(writer: PdfWriter, row: StudioPdfProject) -> None:
    metadata = dict(row.document_metadata or {})
    values: dict[str, str] = {"/Producer": "Ithute Document Studio"}
    mapping = {
        "title": "/Title",
        "author": "/Author",
        "subject": "/Subject",
        "language": "/Lang",
    }
    for key, target in mapping.items():
        if metadata.get(key):
            values[target] = str(metadata[key])
    keywords = metadata.get("keywords") or []
    if keywords:
        values["/Keywords"] = ", ".join(str(item) for item in keywords)
    writer.add_metadata(values)


async def export_pdf_project(
    session: AsyncSession,
    row: StudioPdfProject,
    profile: PdfExportProfile | None = None,
) -> bytes:
    source = _source_path(row)
    page_order = _validate_page_order(list(row.page_order or []), row.page_count)
    objects = [PdfEditLayer.model_validate(item) for item in (row.objects or row.edits or [])]
    edits_by_page: dict[int, list[PdfEditLayer]] = {}
    for edit in objects:
        edits_by_page.setdefault(edit.page, []).append(edit)

    assets = (
        await session.execute(
            select(StudioPdfAsset).where(StudioPdfAsset.project_id == row.id)
        )
    ).scalars().all()
    storage = get_pdf_storage()
    asset_bytes: dict[str, bytes] = {}
    for asset in assets:
        try:
            asset_bytes[str(asset.id)] = storage.get_bytes(asset.storage_key)
        except StorageError:
            continue

    reader = PdfReader(str(source))
    writer = PdfWriter()
    for source_index in page_order:
        writer.add_page(reader.pages[source_index])
        output_page = writer.pages[-1]
        page_width = float(output_page.mediabox.width)
        page_height = float(output_page.mediabox.height)
        layers = edits_by_page.get(source_index, [])
        if layers:
            overlay_bytes = _build_overlay(
                page_width,
                page_height,
                layers,
                asset_bytes,
            )
            overlay_page = PdfReader(io.BytesIO(overlay_bytes)).pages[0]
            output_page.merge_page(overlay_page, over=True)
        rotation = int((row.page_rotations or {}).get(str(source_index), 0))
        if rotation:
            output_page.rotate(rotation)

    _apply_document_metadata(writer, row)
    output = io.BytesIO()
    writer.write(output)
    content = output.getvalue()
    selected_profile = profile or row.default_export_profile or "standard"
    await create_job(
        session,
        project_id=row.id,
        kind="export",
        status="completed",
        progress=100,
        payload={"profile": selected_profile},
        result={"bytes": len(content), "sha256": sha256_bytes(content)},
    )
    await add_audit_event(
        session,
        project_id=row.id,
        action="pdf.exported",
        details={
            "profile": selected_profile,
            "bytes": len(content),
            "sha256": sha256_bytes(content),
        },
    )
    await session.commit()
    return content


async def project_revisions(session: AsyncSession, row: StudioPdfProject) -> list[JsonObject]:
    return await list_revisions(session, row.id)


async def project_audit(session: AsyncSession, row: StudioPdfProject) -> list[JsonObject]:
    return await list_audit_events(session, row.id)


async def project_jobs(session: AsyncSession, row: StudioPdfProject) -> list[JsonObject]:
    return await list_jobs(session, row.id)


async def add_project_asset(
    session: AsyncSession,
    row: StudioPdfProject,
    *,
    name: str,
    media_type: str,
    content: bytes,
) -> JsonObject:
    settings = get_settings()
    if not content or len(content) > settings.max_pdf_asset_mb * 1024 * 1024:
        raise PdfStudioError(
            f"Asset must be between 1 byte and {settings.max_pdf_asset_mb} MB"
        )
    asset = await create_asset(
        session,
        get_pdf_storage(),
        project_id=row.id,
        name=name,
        media_type=media_type,
        content=content,
    )
    await session.flush()
    await add_audit_event(
        session,
        project_id=row.id,
        action="pdf.asset.added",
        details={"assetId": str(asset.id), "name": asset.name, "size": asset.size},
    )
    await session.commit()
    await session.refresh(asset)
    return asset_payload(asset)


async def project_assets(session: AsyncSession, row: StudioPdfProject) -> list[JsonObject]:
    return await list_assets(session, row.id)


async def get_project_asset(
    session: AsyncSession,
    row: StudioPdfProject,
    asset_id: str,
) -> StudioPdfAsset | None:
    try:
        identifier = uuid.UUID(asset_id)
    except ValueError:
        return None
    asset = await session.get(StudioPdfAsset, identifier)
    if asset is None or asset.project_id != row.id:
        return None
    return asset


async def delete_project_asset(
    session: AsyncSession,
    row: StudioPdfProject,
    asset_id: str,
) -> bool:
    asset = await get_project_asset(session, row, asset_id)
    if asset is None:
        return False
    get_pdf_storage().delete(asset.storage_key)
    await session.delete(asset)
    await add_audit_event(
        session,
        project_id=row.id,
        action="pdf.asset.deleted",
        details={"assetId": str(asset.id), "name": asset.name},
    )
    await session.commit()
    return True
