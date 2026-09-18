"""add pdf access grants and webhook outbox

Revision ID: 20260918_0004
Revises: 20260918_0003
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260918_0004"
down_revision: str | None = "20260918_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "studio_pdf_access_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("principal_type", sa.String(length=32), nullable=False),
        sa.Column("principal_id", sa.String(length=240), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["studio_pdf_projects.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "principal_type",
            "principal_id",
            name="uq_pdf_access_project_principal",
        ),
    )
    op.create_index(
        op.f("ix_studio_pdf_access_grants_project_id"),
        "studio_pdf_access_grants",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_studio_pdf_access_grants_role"),
        "studio_pdf_access_grants",
        ["role"],
        unique=False,
    )
    op.create_index(
        op.f("ix_studio_pdf_access_grants_created_at"),
        "studio_pdf_access_grants",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "studio_pdf_webhook_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("endpoint", sa.String(length=2000), nullable=False),
        sa.Column(
            "events",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["project_id"], ["studio_pdf_projects.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("project_id", "is_active", "created_at", "updated_at"):
        op.create_index(
            op.f(f"ix_studio_pdf_webhook_subscriptions_{column}"),
            "studio_pdf_webhook_subscriptions",
            [column],
            unique=False,
        )

    op.create_table(
        "studio_pdf_webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_name", sa.String(length=96), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.String(length=2000), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["project_id"], ["studio_pdf_projects.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["studio_pdf_webhook_subscriptions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "subscription_id",
        "project_id",
        "event_name",
        "status",
        "created_at",
        "updated_at",
    ):
        op.create_index(
            op.f(f"ix_studio_pdf_webhook_deliveries_{column}"),
            "studio_pdf_webhook_deliveries",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in reversed(
        (
            "subscription_id",
            "project_id",
            "event_name",
            "status",
            "created_at",
            "updated_at",
        )
    ):
        op.drop_index(
            op.f(f"ix_studio_pdf_webhook_deliveries_{column}"),
            table_name="studio_pdf_webhook_deliveries",
        )
    op.drop_table("studio_pdf_webhook_deliveries")

    for column in reversed(("project_id", "is_active", "created_at", "updated_at")):
        op.drop_index(
            op.f(f"ix_studio_pdf_webhook_subscriptions_{column}"),
            table_name="studio_pdf_webhook_subscriptions",
        )
    op.drop_table("studio_pdf_webhook_subscriptions")

    op.drop_index(
        op.f("ix_studio_pdf_access_grants_created_at"),
        table_name="studio_pdf_access_grants",
    )
    op.drop_index(
        op.f("ix_studio_pdf_access_grants_role"),
        table_name="studio_pdf_access_grants",
    )
    op.drop_index(
        op.f("ix_studio_pdf_access_grants_project_id"),
        table_name="studio_pdf_access_grants",
    )
    op.drop_table("studio_pdf_access_grants")
