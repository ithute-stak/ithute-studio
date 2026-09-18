from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any

from app.services.accounting_templates import STYLE_PRESETS
from app.services.lesotho_template_packs import (
    CATALOG_TIMESTAMP,
    LAW_PROFILE_VERSION,
    LAW_SOURCES,
)

Json = dict[str, Any]

PACK_SLUG = "business-invoices-statements"
PACK_NAME = "Invoices & Business Statements"

CUSTOMS_SOURCE: Json = {
    "title": "Customs and Excise Act, 1982",
    "citation": "Act 10 of 1982",
    "authority": "Kingdom of Lesotho",
    "sourceUrl": "https://lesotholii.org/akn/ls/act/1982/10/eng@1969-09-01",
}

# slug, label, kind, prefix
DOCUMENT_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("business-invoice", "Business Invoice", "invoice", "BINV"),
    ("vat-invoice", "VAT Invoice", "invoice", "VAT"),
    ("sales-invoice", "Sales Invoice", "invoice", "SINV"),
    ("service-invoice", "Service Invoice", "invoice", "SRV"),
    ("professional-services-invoice", "Professional Services Invoice", "invoice", "PSI"),
    ("consulting-invoice", "Consulting Invoice", "invoice", "CON"),
    ("recurring-invoice", "Recurring Invoice", "invoice", "REC"),
    ("subscription-invoice", "Subscription Invoice", "invoice", "SUB"),
    ("pro-forma-invoice-business", "Pro Forma Invoice", "invoice", "PRO"),
    ("commercial-invoice-business", "Commercial Invoice", "invoice", "CINV"),
    ("export-invoice", "Export Invoice", "invoice", "EXP"),
    ("deposit-invoice", "Deposit Invoice", "invoice", "DEP"),
    ("advance-invoice", "Advance Invoice", "invoice", "ADV"),
    ("interim-invoice", "Interim Invoice", "invoice", "INT"),
    ("milestone-invoice", "Milestone Invoice", "invoice", "MIL"),
    ("progress-invoice", "Progress Invoice", "invoice", "PRG"),
    ("final-invoice", "Final Invoice", "invoice", "FIN"),
    ("rental-invoice", "Rental Invoice", "invoice", "RNT"),
    ("transport-freight-invoice", "Transport / Freight Invoice", "invoice", "FRT"),
    ("construction-invoice", "Construction Invoice", "invoice", "CNS"),
    ("school-fees-invoice", "School Fees Invoice", "invoice", "SCH"),
    ("clinic-medical-invoice", "Clinic / Medical Invoice", "invoice", "MED"),
    ("hotel-accommodation-invoice", "Hotel / Accommodation Invoice", "invoice", "HOT"),
    ("repair-maintenance-invoice", "Repair / Maintenance Invoice", "invoice", "RPM"),
    ("vehicle-service-invoice", "Vehicle Service Invoice", "invoice", "VSI"),
    ("customer-statement-of-account", "Customer Statement of Account", "statement", "CSA"),
    ("supplier-statement-business", "Supplier Statement", "statement", "SUP"),
    ("account-activity-statement", "Account Activity Statement", "statement", "AAS"),
    ("business-transaction-statement", "Business Transaction Statement", "statement", "BTS"),
    ("payment-statement", "Payment Statement", "statement", "PST"),
    ("sales-statement", "Sales Statement", "statement", "SST"),
    ("purchase-statement", "Purchase Statement", "statement", "PUR"),
    ("daily-sales-summary", "Daily Sales Summary", "statement", "DSS"),
    ("weekly-sales-summary", "Weekly Sales Summary", "statement", "WSS"),
    ("monthly-sales-summary", "Monthly Sales Summary", "statement", "MSS"),
    ("revenue-statement", "Revenue Statement", "statement", "REV"),
    ("expense-statement", "Expense Statement", "statement", "EXS"),
    ("cash-sales-statement", "Cash Sales Statement", "statement", "CSS"),
    ("credit-sales-statement", "Credit Sales Statement", "statement", "CRS"),
    ("commission-statement", "Commission Statement", "statement", "COM"),
    ("remittance-statement", "Remittance Statement", "statement", "REM"),
    ("project-billing-statement", "Project Billing Statement", "statement", "PBS"),
    ("contract-billing-statement", "Contract Billing Statement", "statement", "CBS"),
    ("rental-account-statement", "Rental Account Statement", "statement", "RAS"),
    ("subscription-billing-statement", "Subscription Billing Statement", "statement", "SBS"),
    ("service-usage-statement", "Service Usage Statement", "statement", "SUS"),
    ("business-debt-statement", "Business Debt Statement", "statement", "BDS"),
    ("business-settlement-statement", "Settlement Statement", "statement", "SET"),
    ("account-reconciliation-statement", "Account Reconciliation Statement", "statement", "ARS"),
    ("outstanding-invoice-statement", "Outstanding Invoice Statement", "statement", "OIS"),
)


def _text(value: str, *, bold: bool = False) -> Json:
    node: Json = {"type": "text", "text": value}
    if bold:
        node["marks"] = [{"type": "bold"}]
    return node


def _var(path: str, fmt: str | None = None) -> Json:
    attrs: Json = {"path": path}
    if fmt:
        attrs["format"] = fmt
    return {"type": "variable", "attrs": attrs}


def _p(*nodes: Json, align: str = "left", border: bool = False) -> Json:
    return {
        "type": "paragraph",
        "attrs": {"textAlign": align, **({"border": True} if border else {})},
        "content": list(nodes),
    }


def _h(value: str, level: int = 1) -> Json:
    return {"type": "heading", "attrs": {"level": level}, "content": [_text(value)]}


def _cell(*nodes: Json, header: bool = False) -> Json:
    return {
        "type": "tableHeader" if header else "tableCell",
        "content": [_p(*nodes)],
    }


def _row(*cells: Json) -> Json:
    return {"type": "tableRow", "content": list(cells)}


def _party_table() -> Json:
    return {
        "type": "table",
        "content": [
            _row(
                _cell(_text("FROM / SUPPLIER", bold=True), header=True),
                _cell(_text("BILL TO / CUSTOMER", bold=True), header=True),
            ),
            _row(
                _cell(_var("company.name"), _text("\n"), _var("company.address")),
                _cell(_var("customer.name"), _text("\n"), _var("customer.address")),
            ),
            _row(
                _cell(_text("TIN: ", bold=True), _var("company.tin")),
                _cell(_text("TIN: ", bold=True), _var("customer.tin")),
            ),
            _row(
                _cell(_var("company.phone"), _text(" • "), _var("company.email")),
                _cell(_var("customer.phone"), _text(" • "), _var("customer.email")),
            ),
        ],
    }


def _invoice_details(label: str) -> Json:
    return {
        "type": "table",
        "content": [
            _row(
                _cell(_text("Invoice No.", bold=True)),
                _cell(_var("document.number")),
                _cell(_text("Issue date", bold=True)),
                _cell(_var("document.date", "date")),
            ),
            _row(
                _cell(_text("Supply date", bold=True)),
                _cell(_var("document.supplyDate", "date")),
                _cell(_text("Due date", bold=True)),
                _cell(_var("document.dueDate", "date")),
            ),
            _row(
                _cell(_text("Reference", bold=True)),
                _cell(_var("document.reference")),
                _cell(_text("Currency", bold=True)),
                _cell(_var("document.currency")),
            ),
            _row(
                _cell(_text("Document type", bold=True)),
                _cell(_text(label)),
                _cell(_text("Purchase order", bold=True)),
                _cell(_var("document.purchaseOrder")),
            ),
        ],
    }


def _invoice_table() -> Json:
    return {
        "type": "dynamicTable",
        "attrs": {
            "collectionPath": "items",
            "columns": [
                {"label": "Description", "path": "description"},
                {"label": "Qty", "path": "quantity"},
                {"label": "Unit price", "path": "unitPrice", "format": "currency"},
                {"label": "VAT rate", "path": "taxRate"},
                {"label": "VAT", "path": "tax", "format": "currency"},
                {"label": "Amount", "path": "total", "format": "currency"},
            ],
        },
    }


def _invoice_body(label: str, slug: str) -> Json:
    content: list[Json] = [
        _h(label),
        _p(_text("Kingdom of Lesotho • Professional business billing document", bold=True)),
        _party_table(),
        _h("Invoice details", 2),
        _invoice_details(label),
        _h("Goods / services supplied", 2),
        _invoice_table(),
        _p(_text("Subtotal: ", bold=True), _var("totals.subtotal", "currency"), align="right"),
        _p(_text("Discount: ", bold=True), _var("totals.discount", "currency"), align="right"),
        _p(_text("VAT / tax: ", bold=True), _var("totals.tax", "currency"), align="right"),
        _p(_text("Grand total: ", bold=True), _var("totals.total", "currency"), align="right", border=True),
        _p(_text("Amount paid: ", bold=True), _var("totals.amountPaid", "currency"), align="right"),
        _p(_text("Balance due: ", bold=True), _var("totals.balanceDue", "currency"), align="right", border=True),
        _h("Payment instructions", 2),
        _p(_text("Bank / method: ", bold=True), _var("payment.method")),
        _p(_text("Account / mobile number: ", bold=True), _var("payment.account")),
        _p(_text("Payment reference: ", bold=True), _var("payment.reference")),
        _h("Terms and notes", 2),
        _p(_var("document.terms"), border=True),
    ]
    if slug == "vat-invoice":
        content.extend(
            [
                _h("VAT invoice notice", 2),
                _p(
                    _text(
                        "VALUE ADDED TAX INVOICE. Confirm supplier and recipient commercial details/TIN, unique invoice number, issue and supply dates, description and quantity/volume, and VAT-inclusive or VAT-exclusive consideration and tax particulars before issue."
                    ),
                    border=True,
                ),
            ]
        )
    if slug == "export-invoice":
        content.extend(
            [
                _h("Export / customs particulars", 2),
                _p(_text("Country of destination: ", bold=True), _var("export.destination")),
                _p(_text("Country of origin: ", bold=True), _var("export.origin")),
                _p(_text("Customs / tariff reference: ", bold=True), _var("export.customsReference")),
                _p(_text("Freight / insurance terms: ", bold=True), _var("export.freightTerms")),
            ]
        )
    content.extend(
        [
            _p(_text("Verification code: ", bold=True), _var("verification.code")),
            {"type": "qrCode", "attrs": {"value": "{{verification.url}}", "label": "Verify this invoice"}},
        ]
    )
    return {"type": "doc", "content": content}


def _statement_summary(label: str) -> Json:
    return {
        "type": "table",
        "content": [
            _row(
                _cell(_text("Statement", bold=True)),
                _cell(_text(label)),
                _cell(_text("Statement No.", bold=True)),
                _cell(_var("document.number")),
            ),
            _row(
                _cell(_text("Period from", bold=True)),
                _cell(_var("statement.periodStart", "date")),
                _cell(_text("Period to", bold=True)),
                _cell(_var("statement.periodEnd", "date")),
            ),
            _row(
                _cell(_text("Account", bold=True)),
                _cell(_var("customer.accountNumber")),
                _cell(_text("Currency", bold=True)),
                _cell(_var("document.currency")),
            ),
        ],
    }


def _statement_body(label: str) -> Json:
    return {
        "type": "doc",
        "content": [
            _h(label),
            _p(_text("Kingdom of Lesotho • Business account statement", bold=True)),
            _party_table(),
            _h("Statement information", 2),
            _statement_summary(label),
            _h("Account summary", 2),
            _p(_text("Opening balance: ", bold=True), _var("statement.openingBalance", "currency")),
            _p(_text("Total debits / charges: ", bold=True), _var("statement.totalDebits", "currency")),
            _p(_text("Total credits / payments: ", bold=True), _var("statement.totalCredits", "currency")),
            _p(_text("Closing balance: ", bold=True), _var("statement.closingBalance", "currency"), border=True),
            _h("Transactions", 2),
            {
                "type": "dynamicTable",
                "attrs": {
                    "collectionPath": "transactions",
                    "columns": [
                        {"label": "Date", "path": "date", "format": "date"},
                        {"label": "Reference", "path": "reference"},
                        {"label": "Description", "path": "description"},
                        {"label": "Debit", "path": "debit", "format": "currency"},
                        {"label": "Credit", "path": "credit", "format": "currency"},
                        {"label": "Balance", "path": "balance", "format": "currency"},
                    ],
                },
            },
            _h("Ageing / outstanding position", 2),
            {
                "type": "table",
                "content": [
                    _row(
                        _cell(_text("Current", bold=True), header=True),
                        _cell(_text("31–60", bold=True), header=True),
                        _cell(_text("61–90", bold=True), header=True),
                        _cell(_text("90+", bold=True), header=True),
                        _cell(_text("Outstanding", bold=True), header=True),
                    ),
                    _row(
                        _cell(_var("ageing.current", "currency")),
                        _cell(_var("ageing.days60", "currency")),
                        _cell(_var("ageing.days90", "currency")),
                        _cell(_var("ageing.days90Plus", "currency")),
                        _cell(_var("ageing.total", "currency")),
                    ),
                ],
            },
            _h("Notes", 2),
            _p(_var("document.notes"), border=True),
            _p(_text("Verification code: ", bold=True), _var("verification.code")),
            {"type": "qrCode", "attrs": {"value": "{{verification.url}}", "label": "Verify this statement"}},
        ],
    }


def _header(label: str) -> Json:
    return {
        "type": "doc",
        "content": [
            _p(_var("company.name")),
            _p(_text(PACK_NAME.upper(), bold=True)),
            _p(_text(label, bold=True)),
        ],
    }


def _footer() -> Json:
    return {
        "type": "doc",
        "content": [
            _p(_text("Kingdom of Lesotho • "), _text(PACK_NAME), _text(" • "), _text(LAW_PROFILE_VERSION)),
            _p(_var("company.address"), _text(" • "), _var("company.phone"), _text(" • "), _var("company.email")),
            _p(_text("Document "), _var("document.number"), _text(" • Verify "), _var("verification.code")),
        ],
    }


def _laws(slug: str) -> list[Json]:
    laws = [
        deepcopy(LAW_SOURCES["companies-2011"]),
        deepcopy(LAW_SOURCES["data-protection-2012"]),
        deepcopy(LAW_SOURCES["vat-2001"]),
    ]
    if slug == "export-invoice":
        laws.append(deepcopy(CUSTOMS_SOURCE))
    return laws


def _checks(kind: str, slug: str) -> list[str]:
    common = [
        "Use the correct registered/commercial business name and accurate customer/account details.",
        "Protect customer, supplier and transaction personal information under the Data Protection Act 2012.",
        "Keep issued business records and supporting accounting records complete, accurate and auditable.",
    ]
    if kind == "invoice":
        common.extend(
            [
                "Only state VAT as charged where the supplier is lawfully entitled to do so and the supply is treated correctly for VAT purposes.",
                "For a VAT invoice, include the particulars required by section 24 and Schedule III of the Value Added Tax Act 2001, including supplier/recipient commercial details and TINs, unique invoice number/date, supply description/date, quantity or volume, and tax/consideration particulars.",
                "Where prices are VAT-inclusive or VAT-exclusive, disclose that treatment and the applicable tax rate clearly.",
            ]
        )
    else:
        common.extend(
            [
                "Statement balances must reconcile to the source ledger and should not be presented as audited financial statements unless they have actually been audited.",
                "Show the statement period, opening position, movements and closing/outstanding position clearly.",
            ]
        )
    if slug == "export-invoice":
        common.append(
            "Validate export/customs descriptions, values, origin, destination and any prescribed customs invoice particulars before issue."
        )
    return common


def _template(slug: str, label: str, kind: str, prefix: str, style: Json) -> Json:
    template_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"https://ithute.studio/templates/lesotho/{PACK_SLUG}/{slug}/{style['slug']}",
        )
    )
    document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{template_id}/document"))
    compliance = {
        "jurisdiction": "Kingdom of Lesotho",
        "profileVersion": LAW_PROFILE_VERSION,
        "verifiedAt": "2026-09-18",
        "riskLevel": "medium",
        "legalReviewRequired": slug in {"vat-invoice", "export-invoice", "construction-invoice"},
        "laws": _laws(slug),
        "requiredChecks": _checks(kind, slug),
        "note": "Business-document compliance profile. Tax status, VAT registration, customs treatment and underlying ledger data must be validated before issue.",
    }
    document = {
        "schemaVersion": 1,
        "id": document_id,
        "workspaceId": "system",
        "templateId": template_id,
        "properties": {
            "title": label,
            "subject": f"{PACK_NAME} — {label}",
            "author": "Ithute Document Studio",
            "category": PACK_NAME,
            "keywords": ["Lesotho", PACK_SLUG, slug, style["slug"]],
            "language": "en",
        },
        "settings": {
            "pageSize": "a4",
            "orientation": "portrait",
            "marginsMm": {"top": 20, "right": 16, "bottom": 18, "left": 16},
            "columns": 1,
            "headerDistanceMm": 7,
            "footerDistanceMm": 7,
            "showRulers": True,
            "pageNumbering": {"enabled": True, "startAt": 1, "format": "1", "position": "footer"},
        },
        "design": {
            "preset": style["slug"],
            "primaryColor": style["primaryColor"],
            "secondaryColor": style["secondaryColor"],
            "accentColor": style["accentColor"],
            "textColor": style["textColor"],
            "mutedColor": style["mutedColor"],
            "borderColor": style["borderColor"],
            "fontFamily": style["fontFamily"],
            "headerStyle": style["headerStyle"],
            "footerStyle": style["footerStyle"],
            "documentLabel": label,
            "jurisdictionBadge": "LESOTHO",
            "documentPrefix": prefix,
        },
        "compliance": compliance,
        "header": _header(label),
        "body": _invoice_body(label, slug) if kind == "invoice" else _statement_body(label),
        "footer": _footer(),
        "variables": {},
        "createdAt": CATALOG_TIMESTAMP,
        "updatedAt": CATALOG_TIMESTAMP,
        "version": 1,
    }
    return {
        "id": template_id,
        "workspaceId": None,
        "name": f"{label} — {style['name']}",
        "description": f"Lesotho-aware {label.lower()} with {style['name']} styling and backend-ready business data fields.",
        "category": "business-finance",
        "collection": PACK_NAME,
        "pack": PACK_SLUG,
        "documentType": slug,
        "documentTypeLabel": label,
        "family": kind,
        "stylePreset": style["slug"],
        "styleName": style["name"],
        "style": deepcopy(style),
        "jurisdiction": "LS",
        "compliance": compliance,
        "tags": ["Lesotho", "invoice" if kind == "invoice" else "statement", PACK_SLUG, slug, style["slug"]],
        "isPublished": True,
        "isBuiltIn": True,
        "document": document,
        "createdAt": CATALOG_TIMESTAMP,
        "updatedAt": CATALOG_TIMESTAMP,
    }


def business_document_templates() -> list[Json]:
    return [
        _template(slug, label, kind, prefix, style)
        for slug, label, kind, prefix in DOCUMENT_SPECS
        for style in STYLE_PRESETS
    ]


_BUSINESS_TEMPLATES = business_document_templates()
_BUSINESS_BY_ID = {item["id"]: item for item in _BUSINESS_TEMPLATES}


def list_business_document_templates() -> list[Json]:
    return deepcopy(_BUSINESS_TEMPLATES)


def get_business_document_template(template_id: str) -> Json | None:
    item = _BUSINESS_BY_ID.get(template_id)
    return deepcopy(item) if item else None


def business_document_catalog_metadata() -> Json:
    return {
        "jurisdiction": "Kingdom of Lesotho",
        "lawProfileVersion": LAW_PROFILE_VERSION,
        "pack": PACK_SLUG,
        "name": PACK_NAME,
        "documentTypeCount": len(DOCUMENT_SPECS),
        "styleCount": len(STYLE_PRESETS),
        "templateCount": len(_BUSINESS_TEMPLATES),
        "invoiceTypeCount": sum(1 for _, _, kind, _ in DOCUMENT_SPECS if kind == "invoice"),
        "statementTypeCount": sum(1 for _, _, kind, _ in DOCUMENT_SPECS if kind == "statement"),
        "styles": [deepcopy(style) for style in STYLE_PRESETS],
        "packMetadata": {
            "slug": PACK_SLUG,
            "name": PACK_NAME,
            "category": "business-finance",
            "documentTypeCount": len(DOCUMENT_SPECS),
            "templateCount": len(_BUSINESS_TEMPLATES),
            "riskLevel": "medium",
            "laws": [deepcopy(LAW_SOURCES[key]) for key in ("companies-2011", "data-protection-2012", "vat-2001")],
        },
    }
