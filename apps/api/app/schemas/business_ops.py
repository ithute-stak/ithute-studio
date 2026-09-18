from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

Json = dict[str, Any]


class OrganizationCreate(BaseModel):
    legal_name: str = Field(alias="legalName", min_length=1)
    trading_name: str | None = Field(default=None, alias="tradingName")
    registration_number: str | None = Field(default=None, alias="registrationNumber")
    tin: str | None = None
    vat_number: str | None = Field(default=None, alias="vatNumber")
    vat_registered: bool = Field(default=False, alias="vatRegistered")
    default_currency: str = Field(default="LSL", alias="defaultCurrency", min_length=3, max_length=8)
    profile: Json = Field(default_factory=dict)
    branding: Json = Field(default_factory=dict)
    payment_terms: str | None = Field(default=None, alias="paymentTerms")

    model_config = {"populate_by_name": True}


class PartyCreate(BaseModel):
    organization_id: str = Field(alias="organizationId")
    kind: Literal["customer", "supplier", "both"] = "customer"
    name: str
    registration_number: str | None = Field(default=None, alias="registrationNumber")
    tin: str | None = None
    account_reference: str | None = Field(default=None, alias="accountReference")
    credit_terms: str | None = Field(default=None, alias="creditTerms")
    default_currency: str | None = Field(default=None, alias="defaultCurrency")
    contact: Json = Field(default_factory=dict)
    metadata: Json = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class SequenceCreate(BaseModel):
    organization_id: str = Field(alias="organizationId")
    document_type: str = Field(alias="documentType")
    prefix: str
    branch: str = "main"
    year: int | None = None
    next_number: int = Field(default=1, alias="nextNumber", ge=1)
    padding: int = Field(default=6, ge=3, le=12)

    model_config = {"populate_by_name": True}


class IssueDocumentRequest(BaseModel):
    organization_id: str = Field(alias="organizationId")
    template_id: str = Field(alias="templateId")
    party_id: str | None = Field(default=None, alias="partyId")
    document_type: str | None = Field(default=None, alias="documentType")
    branch: str = "main"
    prefix: str | None = None
    data: Json = Field(default_factory=dict)
    issued_by: str | None = Field(default=None, alias="issuedBy")
    source: Json = Field(default_factory=dict)
    metadata: Json = Field(default_factory=dict)
    relation_parent_id: str | None = Field(default=None, alias="relationParentId")
    relation_type: str | None = Field(default=None, alias="relationType")

    model_config = {"populate_by_name": True}


class StatusChangeRequest(BaseModel):
    status: str
    actor: str | None = None
    comment: str | None = None


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    currency: str | None = None
    reference: str | None = None
    method: str | None = None
    metadata: Json = Field(default_factory=dict)


class RelationCreate(BaseModel):
    parent_id: str = Field(alias="parentId")
    child_id: str = Field(alias="childId")
    relation_type: str = Field(alias="relationType")

    model_config = {"populate_by_name": True}


class ApprovalRuleCreate(BaseModel):
    organization_id: str = Field(alias="organizationId")
    name: str
    document_type: str | None = Field(default=None, alias="documentType")
    min_amount: float | None = Field(default=None, alias="minAmount")
    max_amount: float | None = Field(default=None, alias="maxAmount")
    steps: list[Json] = Field(default_factory=list)
    active: bool = True

    model_config = {"populate_by_name": True}


class ApprovalDecision(BaseModel):
    status: Literal["approved", "rejected"]
    actor: str
    comment: str | None = None
    signature: Json = Field(default_factory=dict)


class RecurringCreate(BaseModel):
    organization_id: str = Field(alias="organizationId")
    template_id: str = Field(alias="templateId")
    document_type: str = Field(alias="documentType")
    party_id: str | None = Field(default=None, alias="partyId")
    frequency: Literal["daily", "weekly", "monthly", "yearly"]
    interval: int = Field(default=1, ge=1)
    next_run_date: date = Field(alias="nextRunDate")
    end_date: date | None = Field(default=None, alias="endDate")
    data: Json = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class DeliveryCreate(BaseModel):
    channel: Literal["email", "share", "download"] = "email"
    recipient: str
    metadata: Json = Field(default_factory=dict)


class DeliveryUpdate(BaseModel):
    status: Literal["queued", "sent", "failed", "cancelled"]
    provider_reference: str | None = Field(default=None, alias="providerReference")
    metadata: Json = Field(default_factory=dict)

    model_config = {"populate_by_name": True}
