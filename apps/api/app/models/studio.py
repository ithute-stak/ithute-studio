import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudioTemplate(Base):
    __tablename__ = "studio_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(80), nullable=False, default="custom", server_default="custom", index=True
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )


class StudioDocument(Base):
    __tablename__ = "studio_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )


class StudioPdfProject(Base):
    __tablename__ = "studio_pdf_projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    source_path: Mapped[str] = mapped_column(String(1200), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_order: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    page_metadata: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    page_rotations: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    edits: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
