"""expand pdf studio platform foundation

Revision ID: 20260918_0003
Revises: 20260918_0002
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260918_0003"
down_revision: str | None = "20260918_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "studio_pdf_projects",
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column("storage_backend", sa.String(length=32), server_default="local", nullable=False),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column("source_key", sa.String(length=1200), server_default="", nullable=False),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column("source_sha256", sa.String(length=64), server_default="", nullable=False),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column("source_size", sa.BigInteger(), server_default="0", nullable=False),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column(
            "objects",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column(
            "object_index",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column(
            "font_catalog",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column(
            "security",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column(
            "import_state",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "studio_pdf_projects",
        sa.Column(
            "default_export_profile",
            sa.String(length=32),
            server_default="standard",
            nullable=False,
        ),
    )
    op.execute("UPDATE studio_pdf_projects SET objects = edits")
    op.create_index(
        op.f("ix_studio_pdf_projects_workspace_id"),
        "studio_pdf_projects",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_studio_pdf_projects_status"),
        "studio_pdf_projects",
        ["status"],
        unique=False,
    )

    op.create_table(
        "studio_pdf_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["studio_pdf_projects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "version",
            name="uq_pdf_revision_project_version",
        ),
    )
    op.create_index(
        op.f("ix_studio_pdf_revisions_project_id"),
        "studio_pdf_revisions",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_studio_pdf_revisions_created_at"),
        "studio_pdf_revisions",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "studio_pdf_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("media_type", sa.String(length=160), nullable=False),
        sa.Column("storage_key", sa.String(length=1200), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["studio_pdf_projects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_studio_pdf_assets_project_id"), "studio_pdf_assets", ["project_id"], unique=False)
    op.create_index(op.f("ix_studio_pdf_assets_sha256"), "studio_pdf_assets", ["sha256"], unique=False)
    op.create_index(op.f("ix_studio_pdf_assets_created_at"), "studio_pdf_assets", ["created_at"], unique=False)

    op.create_table(
        "studio_pdf_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("progress", sa.Integer(), server_default="0", nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("error", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["studio_pdf_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_studio_pdf_jobs_project_id"), "studio_pdf_jobs", ["project_id"], unique=False)
    op.create_index(op.f("ix_studio_pdf_jobs_kind"), "studio_pdf_jobs", ["kind"], unique=False)
    op.create_index(op.f("ix_studio_pdf_jobs_status"), "studio_pdf_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_studio_pdf_jobs_created_at"), "studio_pdf_jobs", ["created_at"], unique=False)

    op.create_table(
        "studio_pdf_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=96), nullable=False),
        sa.Column("actor", sa.String(length=240), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["studio_pdf_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_studio_pdf_audit_events_project_id"), "studio_pdf_audit_events", ["project_id"], unique=False)
    op.create_index(op.f("ix_studio_pdf_audit_events_action"), "studio_pdf_audit_events", ["action"], unique=False)
    op.create_index(op.f("ix_studio_pdf_audit_events_created_at"), "studio_pdf_audit_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_studio_pdf_audit_events_created_at"), table_name="studio_pdf_audit_events")
    op.drop_index(op.f("ix_studio_pdf_audit_events_action"), table_name="studio_pdf_audit_events")
    op.drop_index(op.f("ix_studio_pdf_audit_events_project_id"), table_name="studio_pdf_audit_events")
    op.drop_table("studio_pdf_audit_events")

    op.drop_index(op.f("ix_studio_pdf_jobs_created_at"), table_name="studio_pdf_jobs")
    op.drop_index(op.f("ix_studio_pdf_jobs_status"), table_name="studio_pdf_jobs")
    op.drop_index(op.f("ix_studio_pdf_jobs_kind"), table_name="studio_pdf_jobs")
    op.drop_index(op.f("ix_studio_pdf_jobs_project_id"), table_name="studio_pdf_jobs")
    op.drop_table("studio_pdf_jobs")

    op.drop_index(op.f("ix_studio_pdf_assets_created_at"), table_name="studio_pdf_assets")
    op.drop_index(op.f("ix_studio_pdf_assets_sha256"), table_name="studio_pdf_assets")
    op.drop_index(op.f("ix_studio_pdf_assets_project_id"), table_name="studio_pdf_assets")
    op.drop_table("studio_pdf_assets")

    op.drop_index(op.f("ix_studio_pdf_revisions_created_at"), table_name="studio_pdf_revisions")
    op.drop_index(op.f("ix_studio_pdf_revisions_project_id"), table_name="studio_pdf_revisions")
    op.drop_table("studio_pdf_revisions")

    op.drop_index(op.f("ix_studio_pdf_projects_status"), table_name="studio_pdf_projects")
    op.drop_index(op.f("ix_studio_pdf_projects_workspace_id"), table_name="studio_pdf_projects")
    op.drop_column("studio_pdf_projects", "default_export_profile")
    op.drop_column("studio_pdf_projects", "import_state")
    op.drop_column("studio_pdf_projects", "security")
    op.drop_column("studio_pdf_projects", "metadata")
    op.drop_column("studio_pdf_projects", "font_catalog")
    op.drop_column("studio_pdf_projects", "object_index")
    op.drop_column("studio_pdf_projects", "objects")
    op.drop_column("studio_pdf_projects", "source_size")
    op.drop_column("studio_pdf_projects", "source_sha256")
    op.drop_column("studio_pdf_projects", "source_key")
    op.drop_column("studio_pdf_projects", "storage_backend")
    op.drop_column("studio_pdf_projects", "status")
    op.drop_column("studio_pdf_projects", "schema_version")
    op.drop_column("studio_pdf_projects", "workspace_id")
