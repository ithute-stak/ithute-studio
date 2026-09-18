"""add pdf studio projects

Revision ID: 20260918_0002
Revises: 20260918_0001
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "20260918_0002"
down_revision: str | None = "20260918_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "studio_pdf_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("source_path", sa.String(length=1200), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column(
            "page_order",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "page_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "page_rotations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "edits",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_studio_pdf_projects_name"),
        "studio_pdf_projects",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_studio_pdf_projects_created_at"),
        "studio_pdf_projects",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_studio_pdf_projects_updated_at"),
        "studio_pdf_projects",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_studio_pdf_projects_updated_at"), table_name="studio_pdf_projects")
    op.drop_index(op.f("ix_studio_pdf_projects_created_at"), table_name="studio_pdf_projects")
    op.drop_index(op.f("ix_studio_pdf_projects_name"), table_name="studio_pdf_projects")
    op.drop_table("studio_pdf_projects")
