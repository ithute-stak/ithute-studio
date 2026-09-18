"""align business operations indexes

Revision ID: 20260918_0006
Revises: 20260918_0005
Create Date: 2026-09-18
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260918_0006"
down_revision: str | None = "20260918_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "studio_document_register_studio_document_id_key",
        "studio_document_register",
        type_="unique",
    )
    op.drop_index(
        "ix_studio_document_register_studio_document_id",
        table_name="studio_document_register",
    )
    op.create_index(
        "ix_studio_document_register_studio_document_id",
        "studio_document_register",
        ["studio_document_id"],
        unique=True,
    )
    op.drop_index(
        "ix_studio_recurring_documents_party_id",
        table_name="studio_recurring_documents",
    )


def downgrade() -> None:
    op.create_index(
        "ix_studio_recurring_documents_party_id",
        "studio_recurring_documents",
        ["party_id"],
        unique=False,
    )
    op.drop_index(
        "ix_studio_document_register_studio_document_id",
        table_name="studio_document_register",
    )
    op.create_index(
        "ix_studio_document_register_studio_document_id",
        "studio_document_register",
        ["studio_document_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "studio_document_register_studio_document_id_key",
        "studio_document_register",
        ["studio_document_id"],
    )
