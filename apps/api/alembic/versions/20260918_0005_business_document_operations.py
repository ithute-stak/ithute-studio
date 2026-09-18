"""add business document operations

Revision ID: 20260918_0005
Revises: 20260918_0004
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260918_0005"
down_revision: str | None = "20260918_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_OBJECT = sa.text("'{}'::jsonb")
JSON_ARRAY = sa.text("'[]'::jsonb")


def _indexes(table: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column], unique=False)


def upgrade() -> None:
    op.create_table(
        "studio_organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("legal_name", sa.String(240), nullable=False),
        sa.Column("trading_name", sa.String(240), nullable=True),
        sa.Column("registration_number", sa.String(120), nullable=True),
        sa.Column("tin", sa.String(120), nullable=True),
        sa.Column("vat_number", sa.String(120), nullable=True),
        sa.Column("vat_registered", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("default_currency", sa.String(8), server_default="LSL", nullable=False),
        sa.Column("profile", postgresql.JSONB(), server_default=JSON_OBJECT, nullable=False),
        sa.Column("branding", postgresql.JSONB(), server_default=JSON_OBJECT, nullable=False),
        sa.Column("payment_terms", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("studio_organizations", ("legal_name", "created_at", "updated_at"))

    op.create_table(
        "studio_business_parties",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(24), server_default="customer", nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("registration_number", sa.String(120), nullable=True),
        sa.Column("tin", sa.String(120), nullable=True),
        sa.Column("account_reference", sa.String(120), nullable=True),
        sa.Column("credit_terms", sa.String(240), nullable=True),
        sa.Column("default_currency", sa.String(8), nullable=True),
        sa.Column("contact", postgresql.JSONB(), server_default=JSON_OBJECT, nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default=JSON_OBJECT, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["studio_organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "account_reference", name="uq_business_party_org_account_ref"),
    )
    _indexes("studio_business_parties", ("organization_id", "kind", "name", "created_at", "updated_at"))

    op.create_table(
        "studio_document_sequences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch", sa.String(80), server_default="main", nullable=False),
        sa.Column("document_type", sa.String(120), nullable=False),
        sa.Column("prefix", sa.String(24), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("next_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("padding", sa.Integer(), server_default="6", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["studio_organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "branch", "document_type", "year", name="uq_document_sequence_scope"),
    )
    _indexes("studio_document_sequences", ("organization_id", "document_type", "year"))

    op.create_table(
        "studio_document_register",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("party_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("studio_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_number", sa.String(120), nullable=False),
        sa.Column("document_type", sa.String(120), nullable=False),
        sa.Column("status", sa.String(32), server_default="draft", nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("currency", sa.String(8), server_default="LSL", nullable=False),
        sa.Column("subtotal", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("tax", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("total", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("amount_paid", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("balance_due", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("verification_code", sa.String(96), nullable=False),
        sa.Column("issued_by", sa.String(240), nullable=True),
        sa.Column("approved_by", sa.String(240), nullable=True),
        sa.Column("source", postgresql.JSONB(), server_default=JSON_OBJECT, nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default=JSON_OBJECT, nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["studio_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["party_id"], ["studio_business_parties.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["studio_document_id"], ["studio_documents.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("studio_document_id"),
        sa.UniqueConstraint("organization_id", "document_number", name="uq_document_register_org_number"),
        sa.UniqueConstraint("verification_code", name="uq_document_register_verification"),
    )
    _indexes("studio_document_register", ("organization_id", "party_id", "studio_document_id", "template_id", "document_number", "document_type", "status", "issue_date", "due_date", "balance_due", "verification_code", "issued_at", "created_at", "updated_at"))

    op.create_table(
        "studio_document_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("child_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(48), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["studio_document_register.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_id"], ["studio_document_register.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parent_id", "child_id", "relation_type", name="uq_document_relation"),
    )
    _indexes("studio_document_relations", ("parent_id", "child_id", "relation_type"))

    op.create_table(
        "studio_document_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("register_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(8), server_default="LSL", nullable=False),
        sa.Column("reference", sa.String(160), nullable=True),
        sa.Column("method", sa.String(80), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default=JSON_OBJECT, nullable=False),
        sa.ForeignKeyConstraint(["register_id"], ["studio_document_register.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("studio_document_payments", ("register_id", "reference", "paid_at"))

    op.create_table(
        "studio_approval_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("document_type", sa.String(120), nullable=True),
        sa.Column("min_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("max_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("steps", postgresql.JSONB(), server_default=JSON_ARRAY, nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["studio_organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("studio_approval_rules", ("organization_id", "document_type", "active"))

    op.create_table(
        "studio_document_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("register_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(80), nullable=False),
        sa.Column("status", sa.String(24), server_default="pending", nullable=False),
        sa.Column("actor", sa.String(240), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("signature", postgresql.JSONB(), server_default=JSON_OBJECT, nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["register_id"], ["studio_document_register.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["studio_approval_rules.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("register_id", "step_order", name="uq_document_approval_step"),
    )
    _indexes("studio_document_approvals", ("register_id", "status"))

    op.create_table(
        "studio_recurring_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("party_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", sa.String(120), nullable=False),
        sa.Column("frequency", sa.String(24), nullable=False),
        sa.Column("interval", sa.Integer(), server_default="1", nullable=False),
        sa.Column("next_run_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(24), server_default="active", nullable=False),
        sa.Column("data", postgresql.JSONB(), server_default=JSON_OBJECT, nullable=False),
        sa.Column("last_register_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["studio_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["party_id"], ["studio_business_parties.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_register_id"], ["studio_document_register.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("studio_recurring_documents", ("organization_id", "party_id", "template_id", "document_type", "next_run_date", "status"))

    op.create_table(
        "studio_document_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("register_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(24), server_default="email", nullable=False),
        sa.Column("recipient", sa.String(320), nullable=False),
        sa.Column("status", sa.String(24), server_default="queued", nullable=False),
        sa.Column("provider_reference", sa.String(240), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default=JSON_OBJECT, nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["register_id"], ["studio_document_register.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("studio_document_deliveries", ("register_id", "status"))

    op.create_table(
        "studio_verification_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("register_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result", sa.String(24), server_default="verified", nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default=JSON_OBJECT, nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["register_id"], ["studio_document_register.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("studio_verification_events", ("register_id", "verified_at"))


def downgrade() -> None:
    for table in (
        "studio_verification_events",
        "studio_document_deliveries",
        "studio_recurring_documents",
        "studio_document_approvals",
        "studio_approval_rules",
        "studio_document_payments",
        "studio_document_relations",
        "studio_document_register",
        "studio_document_sequences",
        "studio_business_parties",
        "studio_organizations",
    ):
        op.drop_table(table)
