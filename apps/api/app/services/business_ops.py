from __future__ import annotations

import re
import uuid
from copy import deepcopy
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_ops import (
    StudioApprovalRule,
    StudioBusinessParty,
    StudioDocumentApproval,
    StudioDocumentDelivery,
    StudioDocumentPayment,
    StudioDocumentRegister,
    StudioDocumentRelation,
    StudioDocumentSequence,
    StudioOrganization,
    StudioRecurringDocument,
    StudioVerificationEvent,
)
from app.models.studio import StudioDocument
from app.services import studio_store
from app.services.accounting_engine import prepare_accounting_data
from app.template_engine import generate_document

Json = dict[str, Any]
MONEY = Decimal("0.01")

STATUS_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"prepared", "review", "approved", "issued", "cancelled"},
    "prepared": {"review", "approved", "issued", "cancelled"},
    "review": {"approved", "rejected", "cancelled"},
    "rejected": {"prepared", "cancelled"},
    "approved": {"issued", "cancelled"},
    "issued": {"partially-paid", "paid", "overdue", "disputed", "revised", "void"},
    "partially-paid": {"paid", "overdue", "disputed", "void"},
    "overdue": {"partially-paid", "paid", "disputed", "void"},
    "disputed": {"issued", "partially-paid", "paid", "void"},
    "revised": {"void"},
    "paid": {"void"},
    "cancelled": set(),
    "void": set(),
}


def _uuid(value: str | uuid.UUID) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _money(value: object) -> Decimal:
    try:
        return Decimal(str(value or 0)).quantize(MONEY)
    except Exception:
        return Decimal("0.00")


def _iso(value: datetime | date | None) -> str | None:
    return value.isoformat() if value else None


def _date(value: object) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _organization(row: StudioOrganization) -> Json:
    return {
        "id": str(row.id),
        "legalName": row.legal_name,
        "tradingName": row.trading_name,
        "registrationNumber": row.registration_number,
        "tin": row.tin,
        "vatNumber": row.vat_number,
        "vatRegistered": row.vat_registered,
        "defaultCurrency": row.default_currency,
        "profile": row.profile or {},
        "branding": row.branding or {},
        "paymentTerms": row.payment_terms,
        "createdAt": _iso(row.created_at),
        "updatedAt": _iso(row.updated_at),
    }


def _party(row: StudioBusinessParty) -> Json:
    return {
        "id": str(row.id),
        "organizationId": str(row.organization_id),
        "kind": row.kind,
        "name": row.name,
        "registrationNumber": row.registration_number,
        "tin": row.tin,
        "accountReference": row.account_reference,
        "creditTerms": row.credit_terms,
        "defaultCurrency": row.default_currency,
        "contact": row.contact or {},
        "metadata": row.metadata_json or {},
        "createdAt": _iso(row.created_at),
        "updatedAt": _iso(row.updated_at),
    }


def _register(row: StudioDocumentRegister) -> Json:
    return {
        "id": str(row.id),
        "organizationId": str(row.organization_id),
        "partyId": str(row.party_id) if row.party_id else None,
        "studioDocumentId": str(row.studio_document_id),
        "templateId": str(row.template_id) if row.template_id else None,
        "documentNumber": row.document_number,
        "documentType": row.document_type,
        "status": row.status,
        "revision": row.revision,
        "issueDate": _iso(row.issue_date),
        "dueDate": _iso(row.due_date),
        "currency": row.currency,
        "subtotal": float(row.subtotal),
        "tax": float(row.tax),
        "total": float(row.total),
        "amountPaid": float(row.amount_paid),
        "balanceDue": float(row.balance_due),
        "verificationCode": row.verification_code,
        "issuedBy": row.issued_by,
        "approvedBy": row.approved_by,
        "source": row.source or {},
        "metadata": row.metadata_json or {},
        "issuedAt": _iso(row.issued_at),
        "voidedAt": _iso(row.voided_at),
        "createdAt": _iso(row.created_at),
        "updatedAt": _iso(row.updated_at),
    }


async def create_organization(session: AsyncSession, payload: Json) -> Json:
    row = StudioOrganization(
        legal_name=str(payload["legalName"]),
        trading_name=payload.get("tradingName"),
        registration_number=payload.get("registrationNumber"),
        tin=payload.get("tin"),
        vat_number=payload.get("vatNumber"),
        vat_registered=bool(payload.get("vatRegistered", False)),
        default_currency=str(payload.get("defaultCurrency") or "LSL").upper(),
        profile=payload.get("profile") or {},
        branding=payload.get("branding") or {},
        payment_terms=payload.get("paymentTerms"),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _organization(row)


async def list_organizations(session: AsyncSession) -> list[Json]:
    rows = (
        await session.execute(
            select(StudioOrganization).order_by(StudioOrganization.legal_name)
        )
    ).scalars().all()
    return [_organization(row) for row in rows]


async def update_organization(
    session: AsyncSession, organization_id: str, payload: Json
) -> Json | None:
    row = await session.get(StudioOrganization, _uuid(organization_id))
    if row is None:
        return None
    mapping = {
        "legalName": "legal_name",
        "tradingName": "trading_name",
        "registrationNumber": "registration_number",
        "tin": "tin",
        "vatNumber": "vat_number",
        "vatRegistered": "vat_registered",
        "defaultCurrency": "default_currency",
        "profile": "profile",
        "branding": "branding",
        "paymentTerms": "payment_terms",
    }
    for key, attr in mapping.items():
        if key in payload:
            setattr(row, attr, payload[key])
    row.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(row)
    return _organization(row)


async def create_party(session: AsyncSession, payload: Json) -> Json:
    row = StudioBusinessParty(
        organization_id=_uuid(payload["organizationId"]),
        kind=str(payload.get("kind") or "customer"),
        name=str(payload["name"]),
        registration_number=payload.get("registrationNumber"),
        tin=payload.get("tin"),
        account_reference=payload.get("accountReference"),
        credit_terms=payload.get("creditTerms"),
        default_currency=payload.get("defaultCurrency"),
        contact=payload.get("contact") or {},
        metadata_json=payload.get("metadata") or {},
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _party(row)


async def list_parties(
    session: AsyncSession, organization_id: str, kind: str | None = None
) -> list[Json]:
    query = select(StudioBusinessParty).where(
        StudioBusinessParty.organization_id == _uuid(organization_id)
    )
    if kind:
        query = query.where(
            or_(StudioBusinessParty.kind == kind, StudioBusinessParty.kind == "both")
        )
    rows = (
        await session.execute(query.order_by(StudioBusinessParty.name))
    ).scalars().all()
    return [_party(row) for row in rows]


async def put_sequence(session: AsyncSession, payload: Json) -> Json:
    year = int(payload.get("year") or date.today().year)
    branch = str(payload.get("branch") or "main")
    document_type = str(payload["documentType"])
    organization_id = _uuid(payload["organizationId"])
    row = (
        await session.execute(
            select(StudioDocumentSequence).where(
                StudioDocumentSequence.organization_id == organization_id,
                StudioDocumentSequence.branch == branch,
                StudioDocumentSequence.document_type == document_type,
                StudioDocumentSequence.year == year,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = StudioDocumentSequence(
            organization_id=organization_id,
            branch=branch,
            document_type=document_type,
            prefix=str(payload["prefix"]).upper(),
            year=year,
            next_number=int(payload.get("nextNumber") or 1),
            padding=int(payload.get("padding") or 6),
        )
        session.add(row)
    else:
        row.prefix = str(payload.get("prefix") or row.prefix).upper()
        row.next_number = int(payload.get("nextNumber") or row.next_number)
        row.padding = int(payload.get("padding") or row.padding)
        row.updated_at = datetime.now(UTC)
    await session.commit()
    return {
        "id": str(row.id),
        "organizationId": str(row.organization_id),
        "branch": row.branch,
        "documentType": row.document_type,
        "prefix": row.prefix,
        "year": row.year,
        "nextNumber": row.next_number,
        "padding": row.padding,
    }


async def _next_number(
    session: AsyncSession,
    organization_id: uuid.UUID,
    document_type: str,
    prefix: str,
    branch: str,
    year: int,
) -> str:
    row = (
        await session.execute(
            select(StudioDocumentSequence)
            .where(
                StudioDocumentSequence.organization_id == organization_id,
                StudioDocumentSequence.branch == branch,
                StudioDocumentSequence.document_type == document_type,
                StudioDocumentSequence.year == year,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if row is None:
        row = StudioDocumentSequence(
            organization_id=organization_id,
            branch=branch,
            document_type=document_type,
            prefix=prefix.upper(),
            year=year,
            next_number=1,
            padding=6,
        )
        session.add(row)
        await session.flush()
    number = row.next_number
    row.next_number += 1
    row.updated_at = datetime.now(UTC)
    scope = "" if branch == "main" else f"-{re.sub(r'[^A-Za-z0-9]+', '', branch).upper()}"
    return f"{row.prefix}{scope}-{year}-{number:0{row.padding}d}"


def _company_data(row: StudioOrganization) -> Json:
    profile = deepcopy(row.profile or {})
    profile.setdefault("name", row.trading_name or row.legal_name)
    profile.setdefault("legalName", row.legal_name)
    profile.setdefault("registrationNumber", row.registration_number or "")
    profile.setdefault("tin", row.tin or "")
    profile.setdefault("vatNumber", row.vat_number or "")
    profile.setdefault("vatRegistered", row.vat_registered)
    profile.setdefault("branding", deepcopy(row.branding or {}))
    return profile


def _party_data(row: StudioBusinessParty) -> Json:
    contact = deepcopy(row.contact or {})
    result = {
        "name": row.name,
        "registrationNumber": row.registration_number or "",
        "tin": row.tin or "",
        "accountReference": row.account_reference or "",
        "creditTerms": row.credit_terms or "",
    }
    result.update(contact)
    return result


async def _matching_rule(
    session: AsyncSession,
    organization_id: uuid.UUID,
    document_type: str,
    total: Decimal,
) -> StudioApprovalRule | None:
    rules = (
        await session.execute(
            select(StudioApprovalRule)
            .where(
                StudioApprovalRule.organization_id == organization_id,
                StudioApprovalRule.active.is_(True),
                or_(
                    StudioApprovalRule.document_type.is_(None),
                    StudioApprovalRule.document_type == document_type,
                ),
            )
            .order_by(StudioApprovalRule.document_type.desc().nullslast())
        )
    ).scalars().all()
    for rule in rules:
        if rule.min_amount is not None and total < rule.min_amount:
            continue
        if rule.max_amount is not None and total > rule.max_amount:
            continue
        return rule
    return None


async def issue_document(session: AsyncSession, payload: Json) -> Json:
    organization_id = _uuid(payload["organizationId"])
    organization = await session.get(StudioOrganization, organization_id)
    if organization is None:
        raise ValueError("organization_not_found")
    template = await studio_store.get_template(session, str(payload["templateId"]))
    if template is None:
        raise ValueError("template_not_found")
    party = None
    if payload.get("partyId"):
        party = await session.get(StudioBusinessParty, _uuid(payload["partyId"]))
        if party is None or party.organization_id != organization_id:
            raise ValueError("party_not_found")

    data = deepcopy(payload.get("data") or {})
    data.setdefault("company", _company_data(organization))
    if party:
        party_data = _party_data(party)
        data.setdefault("customer", deepcopy(party_data))
        data.setdefault("counterparty", deepcopy(party_data))
        data.setdefault("recipient", deepcopy(party_data))

    document_type = str(
        payload.get("documentType")
        or template.get("documentType")
        or template.get("category")
        or "document"
    )
    prefix = str(
        payload.get("prefix")
        or template.get("documentPrefix")
        or (template.get("document") or {}).get("design", {}).get("documentPrefix")
        or "DOC"
    )
    document_data = data.setdefault("document", {})
    if not isinstance(document_data, dict):
        document_data = {}
        data["document"] = document_data
    issue_date = _date(document_data.get("date")) or date.today()
    document_number = await _next_number(
        session,
        organization_id,
        document_type,
        prefix,
        str(payload.get("branch") or "main"),
        issue_date.year,
    )
    document_data["number"] = document_number
    document_data.setdefault("date", issue_date.isoformat())
    document_data.setdefault("currency", organization.default_currency)
    if organization.payment_terms:
        document_data.setdefault("terms", organization.payment_terms)

    family = str(template.get("family") or "")
    if family:
        data = prepare_accounting_data(template, data)
        document_data = data["document"]

    verification = data.setdefault("verification", {})
    code = f"ITH-{re.sub(r'[^A-Za-z0-9]', '', document_number)}-{uuid.uuid4().hex[:8].upper()}"
    verification["code"] = code
    verification.setdefault("url", f"https://verify.ithute.co.ls/{code}")

    source = {
        "provider": "ithute-studio",
        "entityType": "official-document",
        "entityId": document_number,
        "metadata": deepcopy(payload.get("source") or {}),
    }
    generated = generate_document(template["document"], data, source)
    studio_id = _uuid(generated["id"])
    now = datetime.now(UTC)
    title = str((generated.get("properties") or {}).get("title") or document_number)
    document_row = StudioDocument(
        id=studio_id,
        title=title,
        version=1,
        payload=generated,
        created_at=now,
        updated_at=now,
    )
    session.add(document_row)

    totals = data.get("totals") if isinstance(data.get("totals"), dict) else {}
    subtotal = _money(totals.get("subtotal"))
    tax = _money(totals.get("tax"))
    total = _money(totals.get("total"))
    amount_paid = _money(totals.get("amountPaid"))
    balance = _money(totals.get("balanceDue"))
    if total and not balance and not amount_paid:
        balance = total

    rule = await _matching_rule(session, organization_id, document_type, total)
    register = StudioDocumentRegister(
        organization_id=organization_id,
        party_id=party.id if party else None,
        studio_document_id=studio_id,
        template_id=_uuid(str(template["id"])),
        document_number=document_number,
        document_type=document_type,
        status="review" if rule and rule.steps else "issued",
        issue_date=issue_date,
        due_date=_date(document_data.get("dueDate")),
        currency=str(document_data.get("currency") or organization.default_currency).upper(),
        subtotal=subtotal,
        tax=tax,
        total=total,
        amount_paid=amount_paid,
        balance_due=balance,
        verification_code=code,
        issued_by=payload.get("issuedBy"),
        source=deepcopy(payload.get("source") or {}),
        metadata_json=deepcopy(payload.get("metadata") or {}),
        issued_at=None if rule and rule.steps else now,
        created_at=now,
        updated_at=now,
    )
    session.add(register)
    await session.flush()

    if rule and rule.steps:
        for index, step in enumerate(rule.steps, start=1):
            role = str(step.get("role") or step.get("name") or f"Approver {index}")
            session.add(
                StudioDocumentApproval(
                    register_id=register.id,
                    rule_id=rule.id,
                    step_order=index,
                    role=role,
                    status="pending",
                )
            )

    if payload.get("relationParentId"):
        session.add(
            StudioDocumentRelation(
                parent_id=_uuid(payload["relationParentId"]),
                child_id=register.id,
                relation_type=str(payload.get("relationType") or "derived-from"),
            )
        )

    await session.commit()
    await session.refresh(register)
    return _register(register)


async def list_register(
    session: AsyncSession,
    organization_id: str,
    status: str | None = None,
    document_type: str | None = None,
    search: str | None = None,
) -> list[Json]:
    query = select(StudioDocumentRegister).where(
        StudioDocumentRegister.organization_id == _uuid(organization_id)
    )
    if status:
        query = query.where(StudioDocumentRegister.status == status)
    if document_type:
        query = query.where(StudioDocumentRegister.document_type == document_type)
    if search:
        needle = f"%{search}%"
        query = query.where(
            or_(
                StudioDocumentRegister.document_number.ilike(needle),
                StudioDocumentRegister.document_type.ilike(needle),
            )
        )
    rows = (
        await session.execute(query.order_by(StudioDocumentRegister.created_at.desc()))
    ).scalars().all()
    return [_register(row) for row in rows]


async def get_register(session: AsyncSession, register_id: str) -> Json | None:
    row = await session.get(StudioDocumentRegister, _uuid(register_id))
    return _register(row) if row else None


async def change_status(
    session: AsyncSession,
    register_id: str,
    new_status: str,
    actor: str | None = None,
    comment: str | None = None,
) -> Json | None:
    row = await session.get(StudioDocumentRegister, _uuid(register_id))
    if row is None:
        return None
    if new_status not in STATUS_TRANSITIONS.get(row.status, set()):
        raise ValueError("invalid_status_transition")
    now = datetime.now(UTC)
    row.status = new_status
    row.updated_at = now
    if new_status == "issued" and row.issued_at is None:
        row.issued_at = now
    if new_status == "void":
        row.voided_at = now
    metadata = deepcopy(row.metadata_json or {})
    history = list(metadata.get("statusHistory") or [])
    history.append(
        {
            "status": new_status,
            "actor": actor,
            "comment": comment,
            "at": now.isoformat(),
        }
    )
    metadata["statusHistory"] = history
    row.metadata_json = metadata
    await session.commit()
    await session.refresh(row)
    return _register(row)


async def add_payment(session: AsyncSession, register_id: str, payload: Json) -> Json:
    register = await session.get(StudioDocumentRegister, _uuid(register_id))
    if register is None:
        raise ValueError("document_not_found")
    amount = _money(payload["amount"])
    payment = StudioDocumentPayment(
        register_id=register.id,
        amount=amount,
        currency=str(payload.get("currency") or register.currency).upper(),
        reference=payload.get("reference"),
        method=payload.get("method"),
        metadata_json=payload.get("metadata") or {},
    )
    session.add(payment)
    register.amount_paid = _money(register.amount_paid + amount)
    register.balance_due = _money(max(Decimal(0), register.total - register.amount_paid))
    if register.balance_due == 0 and register.total > 0:
        register.status = "paid"
    elif register.amount_paid > 0:
        register.status = "partially-paid"
    register.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(payment)
    await session.refresh(register)
    return {
        "payment": {
            "id": str(payment.id),
            "registerId": str(payment.register_id),
            "amount": float(payment.amount),
            "currency": payment.currency,
            "reference": payment.reference,
            "method": payment.method,
            "paidAt": _iso(payment.paid_at),
        },
        "document": _register(register),
    }


async def add_relation(session: AsyncSession, payload: Json) -> Json:
    row = StudioDocumentRelation(
        parent_id=_uuid(payload["parentId"]),
        child_id=_uuid(payload["childId"]),
        relation_type=str(payload["relationType"]),
    )
    session.add(row)
    await session.commit()
    return {
        "id": str(row.id),
        "parentId": str(row.parent_id),
        "childId": str(row.child_id),
        "relationType": row.relation_type,
    }


async def document_relations(session: AsyncSession, register_id: str) -> list[Json]:
    identifier = _uuid(register_id)
    rows = (
        await session.execute(
            select(StudioDocumentRelation).where(
                or_(
                    StudioDocumentRelation.parent_id == identifier,
                    StudioDocumentRelation.child_id == identifier,
                )
            )
        )
    ).scalars().all()
    return [
        {
            "id": str(row.id),
            "parentId": str(row.parent_id),
            "childId": str(row.child_id),
            "relationType": row.relation_type,
        }
        for row in rows
    ]


async def create_approval_rule(session: AsyncSession, payload: Json) -> Json:
    row = StudioApprovalRule(
        organization_id=_uuid(payload["organizationId"]),
        name=str(payload["name"]),
        document_type=payload.get("documentType"),
        min_amount=_money(payload["minAmount"]) if payload.get("minAmount") is not None else None,
        max_amount=_money(payload["maxAmount"]) if payload.get("maxAmount") is not None else None,
        steps=payload.get("steps") or [],
        active=bool(payload.get("active", True)),
    )
    session.add(row)
    await session.commit()
    return {
        "id": str(row.id),
        "organizationId": str(row.organization_id),
        "name": row.name,
        "documentType": row.document_type,
        "minAmount": float(row.min_amount) if row.min_amount is not None else None,
        "maxAmount": float(row.max_amount) if row.max_amount is not None else None,
        "steps": row.steps,
        "active": row.active,
    }


async def list_approvals(session: AsyncSession, register_id: str) -> list[Json]:
    rows = (
        await session.execute(
            select(StudioDocumentApproval)
            .where(StudioDocumentApproval.register_id == _uuid(register_id))
            .order_by(StudioDocumentApproval.step_order)
        )
    ).scalars().all()
    return [
        {
            "id": str(row.id),
            "registerId": str(row.register_id),
            "stepOrder": row.step_order,
            "role": row.role,
            "status": row.status,
            "actor": row.actor,
            "comment": row.comment,
            "signature": row.signature or {},
            "decidedAt": _iso(row.decided_at),
        }
        for row in rows
    ]


async def decide_approval(
    session: AsyncSession, approval_id: str, payload: Json
) -> Json:
    approval = await session.get(StudioDocumentApproval, _uuid(approval_id))
    if approval is None:
        raise ValueError("approval_not_found")
    if approval.status != "pending":
        raise ValueError("approval_already_decided")
    prior = (
        await session.execute(
            select(func.count())
            .select_from(StudioDocumentApproval)
            .where(
                StudioDocumentApproval.register_id == approval.register_id,
                StudioDocumentApproval.step_order < approval.step_order,
                StudioDocumentApproval.status != "approved",
            )
        )
    ).scalar_one()
    if prior:
        raise ValueError("prior_approval_pending")
    now = datetime.now(UTC)
    approval.status = str(payload["status"])
    approval.actor = str(payload["actor"])
    approval.comment = payload.get("comment")
    approval.signature = payload.get("signature") or {}
    approval.decided_at = now
    register = await session.get(StudioDocumentRegister, approval.register_id)
    if register is None:
        raise ValueError("document_not_found")
    if approval.status == "rejected":
        register.status = "rejected"
    else:
        pending = (
            await session.execute(
                select(func.count())
                .select_from(StudioDocumentApproval)
                .where(
                    StudioDocumentApproval.register_id == approval.register_id,
                    StudioDocumentApproval.id != approval.id,
                    StudioDocumentApproval.status != "approved",
                )
            )
        ).scalar_one()
        if not pending:
            register.status = "approved"
            register.approved_by = approval.actor
    register.updated_at = now
    await session.commit()
    return {
        "approval": (await list_approvals(session, str(register.id))),
        "document": _register(register),
    }


def _next_recurring_date(current: date, frequency: str, interval: int) -> date:
    if frequency == "daily":
        return current + timedelta(days=interval)
    if frequency == "weekly":
        return current + timedelta(weeks=interval)
    if frequency == "yearly":
        try:
            return current.replace(year=current.year + interval)
        except ValueError:
            return current.replace(month=2, day=28, year=current.year + interval)
    month_index = current.month - 1 + interval
    year = current.year + month_index // 12
    month = month_index % 12 + 1
    days = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return date(year, month, min(current.day, days[month - 1]))


async def create_recurring(session: AsyncSession, payload: Json) -> Json:
    row = StudioRecurringDocument(
        organization_id=_uuid(payload["organizationId"]),
        party_id=_uuid(payload["partyId"]) if payload.get("partyId") else None,
        template_id=_uuid(payload["templateId"]),
        document_type=str(payload["documentType"]),
        frequency=str(payload["frequency"]),
        interval=int(payload.get("interval") or 1),
        next_run_date=_date(payload["nextRunDate"]),
        end_date=_date(payload.get("endDate")),
        data=payload.get("data") or {},
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _recurring(row)


def _recurring(row: StudioRecurringDocument) -> Json:
    return {
        "id": str(row.id),
        "organizationId": str(row.organization_id),
        "partyId": str(row.party_id) if row.party_id else None,
        "templateId": str(row.template_id),
        "documentType": row.document_type,
        "frequency": row.frequency,
        "interval": row.interval,
        "nextRunDate": _iso(row.next_run_date),
        "endDate": _iso(row.end_date),
        "status": row.status,
        "data": row.data or {},
        "lastRegisterId": str(row.last_register_id) if row.last_register_id else None,
    }


async def due_recurring(session: AsyncSession, organization_id: str) -> list[Json]:
    today = date.today()
    rows = (
        await session.execute(
            select(StudioRecurringDocument).where(
                StudioRecurringDocument.organization_id == _uuid(organization_id),
                StudioRecurringDocument.status == "active",
                StudioRecurringDocument.next_run_date <= today,
                or_(StudioRecurringDocument.end_date.is_(None), StudioRecurringDocument.end_date >= today),
            )
        )
    ).scalars().all()
    return [_recurring(row) for row in rows]


async def run_recurring(session: AsyncSession, recurring_id: str) -> Json:
    row = await session.get(StudioRecurringDocument, _uuid(recurring_id))
    if row is None or row.status != "active":
        raise ValueError("recurring_not_active")
    issued = await issue_document(
        session,
        {
            "organizationId": str(row.organization_id),
            "templateId": str(row.template_id),
            "partyId": str(row.party_id) if row.party_id else None,
            "documentType": row.document_type,
            "data": deepcopy(row.data or {}),
            "source": {"recurringId": str(row.id)},
        },
    )
    row = await session.get(StudioRecurringDocument, row.id)
    if row is None:
        raise ValueError("recurring_not_found")
    row.last_register_id = _uuid(issued["id"])
    row.next_run_date = _next_recurring_date(
        row.next_run_date, row.frequency, row.interval
    )
    if row.end_date and row.next_run_date > row.end_date:
        row.status = "completed"
    row.updated_at = datetime.now(UTC)
    await session.commit()
    return {"recurring": _recurring(row), "document": issued}


async def queue_delivery(session: AsyncSession, register_id: str, payload: Json) -> Json:
    row = StudioDocumentDelivery(
        register_id=_uuid(register_id),
        channel=str(payload.get("channel") or "email"),
        recipient=str(payload["recipient"]),
        metadata_json=payload.get("metadata") or {},
    )
    session.add(row)
    await session.commit()
    return _delivery(row)


def _delivery(row: StudioDocumentDelivery) -> Json:
    return {
        "id": str(row.id),
        "registerId": str(row.register_id),
        "channel": row.channel,
        "recipient": row.recipient,
        "status": row.status,
        "providerReference": row.provider_reference,
        "metadata": row.metadata_json or {},
        "queuedAt": _iso(row.queued_at),
        "sentAt": _iso(row.sent_at),
    }


async def update_delivery(session: AsyncSession, delivery_id: str, payload: Json) -> Json:
    row = await session.get(StudioDocumentDelivery, _uuid(delivery_id))
    if row is None:
        raise ValueError("delivery_not_found")
    row.status = str(payload["status"])
    row.provider_reference = payload.get("providerReference") or row.provider_reference
    metadata = deepcopy(row.metadata_json or {})
    metadata.update(payload.get("metadata") or {})
    row.metadata_json = metadata
    if row.status == "sent":
        row.sent_at = datetime.now(UTC)
    await session.commit()
    return _delivery(row)


async def verify_document(session: AsyncSession, code: str) -> Json | None:
    register = (
        await session.execute(
            select(StudioDocumentRegister).where(
                StudioDocumentRegister.verification_code == code
            )
        )
    ).scalar_one_or_none()
    if register is None:
        return None
    session.add(
        StudioVerificationEvent(register_id=register.id, result="verified")
    )
    await session.commit()
    organization = await session.get(StudioOrganization, register.organization_id)
    return {
        "verified": True,
        "documentNumber": register.document_number,
        "documentType": register.document_type,
        "status": register.status,
        "revision": register.revision,
        "issueDate": _iso(register.issue_date),
        "organization": organization.legal_name if organization else None,
        "verificationCode": register.verification_code,
    }


async def dashboard(session: AsyncSession, organization_id: str) -> Json:
    org_id = _uuid(organization_id)
    rows = (
        await session.execute(
            select(StudioDocumentRegister).where(
                StudioDocumentRegister.organization_id == org_id
            )
        )
    ).scalars().all()
    counts: dict[str, int] = {}
    total_issued = Decimal(0)
    total_outstanding = Decimal(0)
    overdue = 0
    awaiting_approval = 0
    today = date.today()
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
        total_issued += row.total
        total_outstanding += row.balance_due
        if row.due_date and row.due_date < today and row.balance_due > 0:
            overdue += 1
        if row.status == "review":
            awaiting_approval += 1
    verification_count = (
        await session.execute(
            select(func.count())
            .select_from(StudioVerificationEvent)
            .join(
                StudioDocumentRegister,
                StudioDocumentRegister.id == StudioVerificationEvent.register_id,
            )
            .where(StudioDocumentRegister.organization_id == org_id)
        )
    ).scalar_one()
    return {
        "documentCount": len(rows),
        "statusCounts": counts,
        "amountIssued": float(total_issued),
        "amountOutstanding": float(total_outstanding),
        "overdueDocuments": overdue,
        "awaitingApproval": awaiting_approval,
        "verificationCount": int(verification_count),
    }


async def get_official_document(
    session: AsyncSession, register_id: str
) -> tuple[StudioDocumentRegister, StudioDocument] | None:
    register = await session.get(StudioDocumentRegister, _uuid(register_id))
    if register is None:
        return None
    document = await session.get(StudioDocument, register.studio_document_id)
    if document is None:
        return None
    return register, document
