from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from app.services.accounting_templates import FAMILY_TABLES, get_accounting_template
from app.services.business_document_templates import get_business_document_template

Json = dict[str, Any]
MONEY = Decimal("0.01")


def _decimal(value: object, default: str = "0") -> Decimal:
    if value in {None, ""}:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _money(value: Decimal) -> float:
    return float(value.quantize(MONEY, rounding=ROUND_HALF_UP))


def _sales_items(rows: list[object]) -> tuple[list[Json], Json]:
    prepared: list[Json] = []
    subtotal = Decimal(0)
    tax_total = Decimal(0)
    discount_total = Decimal(0)

    for raw in rows:
        row = deepcopy(raw) if isinstance(raw, dict) else {"description": str(raw)}
        quantity = _decimal(row.get("quantity"), "1")
        unit_price = _decimal(row.get("unitPrice"))
        base = quantity * unit_price
        discount = _decimal(row.get("discount"))
        taxable = max(Decimal(0), base - discount)
        if row.get("tax") not in {None, ""}:
            tax = _decimal(row.get("tax"))
        else:
            tax_rate = _decimal(row.get("taxRate"))
            tax = taxable * tax_rate / Decimal(100)
        total = taxable + tax

        row["quantity"] = float(quantity)
        row["unitPrice"] = _money(unit_price)
        row["discount"] = _money(discount)
        row["tax"] = _money(tax)
        row["total"] = _money(total)
        prepared.append(row)
        subtotal += base
        discount_total += discount
        tax_total += tax

    grand_total = subtotal - discount_total + tax_total
    return prepared, {
        "subtotal": _money(subtotal),
        "discount": _money(discount_total),
        "tax": _money(tax_total),
        "total": _money(grand_total),
    }


def _sum_collection(rows: list[object]) -> Decimal:
    total = Decimal(0)
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        for key in ("total", "amount", "current", "bookValue", "net", "debit"):
            if raw.get(key) not in {None, ""}:
                total += _decimal(raw.get(key))
                break
    return total


def _table_family(family: str) -> str:
    return {"invoice": "sales", "statement": "ledger"}.get(family, family)


def prepare_accounting_data(template: Json, incoming: Json) -> Json:
    data = deepcopy(incoming)
    family = str(template.get("family") or "sales")
    document = data.setdefault("document", {})
    if not isinstance(document, dict):
        document = {}
        data["document"] = document
    document.setdefault("date", datetime.now(UTC).date().isoformat())
    document.setdefault("currency", "LSL")

    totals = data.setdefault("totals", {})
    if not isinstance(totals, dict):
        totals = {}
        data["totals"] = totals

    if family in {"sales", "purchase", "invoice"}:
        rows, calculated = _sales_items(
            data.get("items") if isinstance(data.get("items"), list) else []
        )
        data["items"] = rows
        amount_paid = _decimal(totals.get("amountPaid"))
        calculated["amountPaid"] = _money(amount_paid)
        calculated["balanceDue"] = _money(_decimal(calculated["total"]) - amount_paid)
        totals.update(calculated)
    elif family == "receipt":
        payments = data.get("payments") if isinstance(data.get("payments"), list) else []
        totals["total"] = _money(_sum_collection(payments))
        totals["balanceDue"] = 0.0
    elif family == "statement":
        transactions = data.get("transactions") if isinstance(data.get("transactions"), list) else []
        totals.setdefault("total", _money(_sum_collection(transactions)))
        statement = data.setdefault("statement", {})
        if isinstance(statement, dict):
            opening = _decimal(statement.get("openingBalance"))
            debits = sum(
                (_decimal(row.get("debit")) for row in transactions if isinstance(row, dict)),
                Decimal(0),
            )
            credits = sum(
                (_decimal(row.get("credit")) for row in transactions if isinstance(row, dict)),
                Decimal(0),
            )
            statement["totalDebits"] = _money(debits)
            statement["totalCredits"] = _money(credits)
            statement["closingBalance"] = _money(opening + debits - credits)
    else:
        schema = accounting_form_schema(template)
        collection_path = schema.get("collectionPath")
        if collection_path and isinstance(data.get(str(collection_path)), list):
            totals.setdefault(
                "total",
                _money(_sum_collection(data[str(collection_path)])),
            )

    verification = data.setdefault("verification", {})
    if isinstance(verification, dict):
        verification.setdefault("code", "DRAFT")
        verification.setdefault("url", "")
    approval = data.setdefault("approval", {})
    if isinstance(approval, dict):
        approval.setdefault("preparedBy", "")
        approval.setdefault("approvedBy", "")
    return data


def accounting_form_schema(template: Json) -> Json:
    family = str(template.get("family") or "sales")
    table = FAMILY_TABLES.get(_table_family(family))
    collection_path = table[0] if table else None
    columns = []
    if table:
        columns = [
            {"label": label, "path": path, "format": fmt or "text"}
            for label, path, fmt in table[1]
        ]
    if family in {"sales", "purchase", "invoice"}:
        known = {str(item["path"]) for item in columns}
        for extra in (
            {"label": "Tax rate %", "path": "taxRate", "format": "number"},
            {"label": "Discount", "path": "discount", "format": "currency"},
        ):
            if str(extra["path"]) not in known:
                columns.insert(max(len(columns) - 1, 0), extra)

    design = template.get("document", {}).get("design", {})
    prefix = template.get("documentPrefix") or (
        design.get("documentPrefix") if isinstance(design, dict) else None
    )
    return {
        "templateId": template.get("id"),
        "documentType": template.get("documentType"),
        "documentTypeLabel": template.get("documentTypeLabel"),
        "family": family,
        "stylePreset": template.get("stylePreset"),
        "styleName": template.get("styleName"),
        "documentPrefix": prefix,
        "collectionPath": collection_path,
        "collectionColumns": columns,
        "showCounterparty": family not in {"payroll", "payroll-summary"},
        "showLetterFields": family in {"letter", "certificate"},
        "showPayrollFields": family == "payroll",
    }


def get_accounting_form_schema(template_id: str) -> Json | None:
    template = get_accounting_template(template_id) or get_business_document_template(
        template_id
    )
    return accounting_form_schema(template) if template else None
