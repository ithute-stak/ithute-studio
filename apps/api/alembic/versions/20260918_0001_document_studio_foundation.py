"""create document studio foundation

Revision ID: 20260918_0001
Revises:
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260918_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "studio_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column(
            "category",
            sa.String(length=80),
            server_default="custom",
            nullable=False,
        ),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("name", "category", "created_at", "updated_at"):
        op.create_index(
            f"ix_studio_templates_{column}",
            "studio_templates",
            [column],
        )

    op.create_table(
        "studio_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("title", "created_at", "updated_at"):
        op.create_index(
            f"ix_studio_documents_{column}",
            "studio_documents",
            [column],
        )


def downgrade() -> None:
    for column in reversed(("title", "created_at", "updated_at")):
        op.drop_index(
            f"ix_studio_documents_{column}",
            table_name="studio_documents",
        )
    op.drop_table("studio_documents")

    for column in reversed(("name", "category", "created_at", "updated_at")):
        op.drop_index(
            f"ix_studio_templates_{column}",
            table_name="studio_templates",
        )
    op.drop_table("studio_templates")
