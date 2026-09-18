import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudioOrganization(Base):
    __tablename__ = "studio_organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legal_name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    trading_name: Mapped[str | None] = mapped_column(String(240), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tin: Mapped[str | None] = mapped_column(String(120), nullable=True)
    vat_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    vat_registered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    default_currency: Mapped[str] = mapped_column(String(8), nullable=False, default="LSL", server_default="LSL")
    profile: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    branding: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    payment_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)


class StudioBusinessParty(Base):
    __tablename__ = "studio_business_parties"
    __table_args__ = (
        UniqueConstraint("organization_id", "account_reference", name="uq_business_party_org_account_ref"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(24), nullable=False, default="customer", server_default="customer", index=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    registration_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tin: Mapped[str | None] = mapped_column(String(120), nullable=True)
    account_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    credit_terms: Mapped[str | None] = mapped_column(String(240), nullable=True)
    default_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    contact: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)


class StudioDocumentSequence(Base):
    __tablename__ = "studio_document_sequences"
    __table_args__ = (
        UniqueConstraint("organization_id", "branch", "document_type", "year", name="uq_document_sequence_scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    branch: Mapped[str] = mapped_column(String(80), nullable=False, default="main", server_default="main")
    document_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    prefix: Mapped[str] = mapped_column(String(24), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    next_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    padding: Mapped[int] = mapped_column(Integer, nullable=False, default=6, server_default="6")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StudioDocumentRegister(Base):
    __tablename__ = "studio_document_register"
    __table_args__ = (
        UniqueConstraint("organization_id", "document_number", name="uq_document_register_org_number"),
        UniqueConstraint("verification_code", name="uq_document_register_verification"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    party_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_business_parties.id", ondelete="SET NULL"), nullable=True, index=True)
    studio_document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_documents.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    document_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", server_default="draft", index=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="LSL", server_default="LSL")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0, server_default="0")
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0, server_default="0")
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0, server_default="0")
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0, server_default="0")
    balance_due: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0, server_default="0", index=True)
    verification_code: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    issued_by: Mapped[str | None] = mapped_column(String(240), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(240), nullable=True)
    source: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default="{}")
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)


class StudioDocumentRelation(Base):
    __tablename__ = "studio_document_relations"
    __table_args__ = (
        UniqueConstraint("parent_id", "child_id", "relation_type", name="uq_document_relation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_document_register.id", ondelete="CASCADE"), nullable=False, index=True)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_document_register.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StudioDocumentPayment(Base):
    __tablename__ = "studio_document_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    register_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_document_register.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="LSL", server_default="LSL")
    reference: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    method: Mapped[str | None] = mapped_column(String(80), nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default="{}")


class StudioApprovalRule(Base):
    __tablename__ = "studio_approval_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    min_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    steps: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StudioDocumentApproval(Base):
    __tablename__ = "studio_document_approvals"
    __table_args__ = (
        UniqueConstraint("register_id", "step_order", name="uq_document_approval_step"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    register_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_document_register.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_approval_rules.id", ondelete="SET NULL"), nullable=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", server_default="pending", index=True)
    actor: Mapped[str | None] = mapped_column(String(240), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StudioRecurringDocument(Base):
    __tablename__ = "studio_recurring_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    party_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_business_parties.id", ondelete="SET NULL"), nullable=True)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    frequency: Mapped[str] = mapped_column(String(24), nullable=False)
    interval: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    next_run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active", server_default="active", index=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    last_register_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_document_register.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StudioDocumentDelivery(Base):
    __tablename__ = "studio_document_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    register_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_document_register.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(24), nullable=False, default="email", server_default="email")
    recipient: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued", server_default="queued", index=True)
    provider_reference: Mapped[str | None] = mapped_column(String(240), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default="{}")
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StudioVerificationEvent(Base):
    __tablename__ = "studio_verification_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    register_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studio_document_register.id", ondelete="CASCADE"), nullable=False, index=True)
    result: Mapped[str] = mapped_column(String(24), nullable=False, default="verified", server_default="verified")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default="{}")
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
