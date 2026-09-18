from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any

Json = dict[str, Any]

CATALOG_TIMESTAMP = "2026-09-18T00:00:00+00:00"

STYLE_PRESETS: tuple[Json, ...] = (
    {
        "slug": "executive-navy",
        "name": "Executive Navy",
        "description": "Formal corporate layout with a navy masthead and blue accent rules.",
        "primaryColor": "#102A43",
        "secondaryColor": "#D9EAF7",
        "accentColor": "#2F80ED",
        "textColor": "#172B4D",
        "mutedColor": "#627D98",
        "borderColor": "#BCCCDC",
        "fontFamily": "Helvetica",
        "headerStyle": "band",
        "footerStyle": "line",
    },
    {
        "slug": "modern-teal",
        "name": "Modern Teal",
        "description": "Contemporary finance layout with teal blocks and clean information hierarchy.",
        "primaryColor": "#0F766E",
        "secondaryColor": "#CCFBF1",
        "accentColor": "#14B8A6",
        "textColor": "#134E4A",
        "mutedColor": "#5F7472",
        "borderColor": "#99D5CF",
        "fontFamily": "Helvetica",
        "headerStyle": "split",
        "footerStyle": "band",
    },
    {
        "slug": "burgundy-gold",
        "name": "Burgundy & Gold",
        "description": "Premium official-document treatment with burgundy framing and gold highlights.",
        "primaryColor": "#7A1831",
        "secondaryColor": "#F7E7C1",
        "accentColor": "#C9A227",
        "textColor": "#3F1723",
        "mutedColor": "#755965",
        "borderColor": "#D7BE85",
        "fontFamily": "Times-Roman",
        "headerStyle": "left-accent",
        "footerStyle": "double-line",
    },
    {
        "slug": "slate-minimal",
        "name": "Slate Minimal",
        "description": "Restrained monochrome accounting layout for dense reports and professional statements.",
        "primaryColor": "#334155",
        "secondaryColor": "#F1F5F9",
        "accentColor": "#64748B",
        "textColor": "#1E293B",
        "mutedColor": "#64748B",
        "borderColor": "#CBD5E1",
        "fontFamily": "Helvetica",
        "headerStyle": "minimal",
        "footerStyle": "minimal",
    },
    {
        "slug": "emerald-ledger",
        "name": "Emerald Ledger",
        "description": "Ledger-inspired finance layout with emerald headers and balanced report tables.",
        "primaryColor": "#166534",
        "secondaryColor": "#DCFCE7",
        "accentColor": "#22C55E",
        "textColor": "#14532D",
        "mutedColor": "#5B7564",
        "borderColor": "#A7D7B4",
        "fontFamily": "Helvetica",
        "headerStyle": "ledger",
        "footerStyle": "band",
    },
)

# slug, label, family, prefix
DOCUMENT_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("invoice", "Invoice", "sales", "INV"),
    ("tax-invoice", "Tax Invoice", "sales", "TINV"),
    ("commercial-invoice", "Commercial Invoice", "sales", "CINV"),
    ("pro-forma-invoice", "Pro Forma Invoice", "sales", "PRO"),
    ("receipt", "Official Receipt", "receipt", "RCT"),
    ("deposit-receipt", "Deposit Receipt", "receipt", "DRC"),
    ("quotation", "Quotation", "sales", "QUO"),
    ("estimate", "Cost Estimate", "sales", "EST"),
    ("customer-statement", "Customer Statement", "ledger", "CST"),
    ("supplier-statement", "Supplier Statement", "ledger", "SST"),
    ("loan-statement", "Loan Statement", "ledger", "LST"),
    ("transaction-statement", "Transaction Statement", "ledger", "TST"),
    ("credit-note", "Credit Note", "sales", "CN"),
    ("debit-note", "Debit Note", "sales", "DN"),
    ("purchase-order", "Purchase Order", "purchase", "PO"),
    ("delivery-note", "Delivery Note", "stock", "DNTE"),
    ("goods-received-note", "Goods Received Note", "stock", "GRN"),
    ("payment-voucher", "Payment Voucher", "voucher", "PV"),
    ("petty-cash-voucher", "Petty Cash Voucher", "voucher", "PCV"),
    ("expense-claim", "Expense Claim", "voucher", "EXP"),
    ("cashbook-report", "Cashbook Report", "ledger", "CB"),
    ("general-ledger", "General Ledger", "ledger", "GL"),
    ("trial-balance", "Trial Balance", "financial", "TB"),
    ("income-statement", "Income Statement", "financial", "IS"),
    ("balance-sheet", "Statement of Financial Position", "financial", "SFP"),
    ("cash-flow-statement", "Cash Flow Statement", "financial", "CFS"),
    ("accounts-receivable-ageing", "Accounts Receivable Ageing", "ageing", "ARA"),
    ("accounts-payable-ageing", "Accounts Payable Ageing", "ageing", "APA"),
    ("bank-reconciliation", "Bank Reconciliation Statement", "reconciliation", "BRS"),
    ("payslip", "Payslip", "payroll", "PAY"),
    ("payroll-summary", "Payroll Summary", "payroll-summary", "PRS"),
    ("tax-vat-schedule", "Tax / VAT Schedule", "tax", "TAX"),
    ("budget-vs-actual", "Budget vs Actual Report", "financial", "BVA"),
    ("journal-voucher", "Journal Voucher", "journal", "JV"),
    ("asset-register", "Fixed Asset Register", "asset", "FAR"),
    ("inventory-report", "Inventory / Stock Report", "stock", "INVSTK"),
    ("debt-collection-statement", "Debt Collection Statement", "ledger", "DCS"),
    ("settlement-letter", "Settlement Letter", "letter", "SET"),
    ("account-balance-confirmation", "Account Balance Confirmation", "letter", "ABC"),
    ("payment-confirmation", "Payment Confirmation", "letter", "PC"),
    ("account-clearance-certificate", "Account Clearance Certificate", "certificate", "ACC"),
)

FAMILY_TABLES: dict[str, tuple[str, tuple[tuple[str, str, str | None], ...]]] = {
    "sales": (
        "items",
        (("Description", "description", None), ("Qty", "quantity", None), ("Unit price", "unitPrice", "currency"), ("Tax", "tax", "currency"), ("Amount", "total", "currency")),
    ),
    "receipt": (
        "payments",
        (("Reference", "reference", None), ("Description", "description", None), ("Method", "method", None), ("Amount", "amount", "currency")),
    ),
    "purchase": (
        "items",
        (("Item / service", "description", None), ("Qty", "quantity", None), ("Unit price", "unitPrice", "currency"), ("Amount", "total", "currency")),
    ),
    "stock": (
        "items",
        (("Code", "code", None), ("Description", "description", None), ("Qty", "quantity", None), ("Unit", "unit", None), ("Value", "total", "currency")),
    ),
    "voucher": (
        "expenses",
        (("Date", "date", "date"), ("Reference", "reference", None), ("Description", "description", None), ("Amount", "amount", "currency")),
    ),
    "ledger": (
        "transactions",
        (("Date", "date", "date"), ("Reference", "reference", None), ("Description", "description", None), ("Debit", "debit", "currency"), ("Credit", "credit", "currency"), ("Balance", "balance", "currency")),
    ),
    "financial": (
        "accounts",
        (("Account", "account", None), ("Description", "description", None), ("Current period", "current", "currency"), ("Prior period", "prior", "currency")),
    ),
    "ageing": (
        "accounts",
        (("Account", "name", None), ("Current", "current", "currency"), ("31–60 days", "days60", "currency"), ("61–90 days", "days90", "currency"), ("90+ days", "days90Plus", "currency"), ("Total", "total", "currency")),
    ),
    "reconciliation": (
        "reconciliationItems",
        (("Reference", "reference", None), ("Description", "description", None), ("Book", "bookAmount", "currency"), ("Bank", "bankAmount", "currency"), ("Difference", "difference", "currency")),
    ),
    "payroll-summary": (
        "employees",
        (("Employee", "name", None), ("Gross", "gross", "currency"), ("Deductions", "deductions", "currency"), ("Net pay", "net", "currency")),
    ),
    "tax": (
        "taxLines",
        (("Tax code", "code", None), ("Description", "description", None), ("Taxable value", "taxable", "currency"), ("Tax", "tax", "currency"), ("Total", "total", "currency")),
    ),
    "journal": (
        "entries",
        (("Account", "account", None), ("Description", "description", None), ("Debit", "debit", "currency"), ("Credit", "credit", "currency")),
    ),
    "asset": (
        "assets",
        (("Asset ID", "code", None), ("Description", "description", None), ("Acquired", "acquiredDate", "date"), ("Cost", "cost", "currency"), ("Depreciation", "depreciation", "currency"), ("Book value", "bookValue", "currency")),
    ),
}


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


def _paragraph(*nodes: Json, align: str = "left", shading: str | None = None, border: bool = False) -> Json:
    attrs: Json = {"textAlign": align}
    if shading:
        attrs["shading"] = shading
    if border:
        attrs["border"] = True
    return {"type": "paragraph", "attrs": attrs, "content": list(nodes)}


def _heading(text: str, level: int = 1, align: str = "left") -> Json:
    return {"type": "heading", "attrs": {"level": level, "textAlign": align}, "content": [_text(text)]}


def _cell(*nodes: Json, header: bool = False) -> Json:
    return {
        "type": "tableHeader" if header else "tableCell",
        "content": [_paragraph(*nodes)],
    }


def _row(*cells: Json) -> Json:
    return {"type": "tableRow", "content": list(cells)}


def _info_table(spec_name: str) -> Json:
    return {
        "type": "table",
        "content": [
            _row(
                _cell(_text("Document No.", bold=True)),
                _cell(_var("document.number")),
                _cell(_text("Date", bold=True)),
                _cell(_var("document.date", "date")),
            ),
            _row(
                _cell(_text("Reference", bold=True)),
                _cell(_var("document.reference")),
                _cell(_text("Currency", bold=True)),
                _cell(_var("document.currency")),
            ),
            _row(
                _cell(_text("Account / Party", bold=True)),
                _cell(_var("counterparty.name")),
                _cell(_text("Document", bold=True)),
                _cell(_text(spec_name)),
            ),
        ],
    }


def _dynamic_table(family: str) -> Json | None:
    table = FAMILY_TABLES.get(family)
    if table is None:
        return None
    collection, columns = table
    return {
        "type": "dynamicTable",
        "attrs": {
            "collectionPath": collection,
            "columns": [
                {"label": label, "path": path, **({"format": fmt} if fmt else {})}
                for label, path, fmt in columns
            ],
        },
    }


def _totals_block(family: str) -> list[Json]:
    if family in {"sales", "purchase"}:
        return [
            _paragraph(_text("Subtotal: ", bold=True), _var("totals.subtotal", "currency"), align="right"),
            _paragraph(_text("Tax: ", bold=True), _var("totals.tax", "currency"), align="right"),
            _paragraph(_text("Total: ", bold=True), _var("totals.total", "currency"), align="right", border=True),
            _paragraph(_text("Balance due: ", bold=True), _var("totals.balanceDue", "currency"), align="right"),
        ]
    if family == "receipt":
        return [_paragraph(_text("Amount received: ", bold=True), _var("totals.total", "currency"), align="right", border=True)]
    if family in {"voucher", "journal", "payroll-summary", "tax", "asset", "stock", "ageing", "ledger", "financial", "reconciliation"}:
        return [_paragraph(_text("Report total: ", bold=True), _var("totals.total", "currency"), align="right", border=True)]
    return []


def _payroll_body(style: Json) -> list[Json]:
    return [
        _heading("Employee & Payroll Details", 2),
        _info_table("Payslip"),
        _paragraph(_text("Employee: ", bold=True), _var("employee.name")),
        _paragraph(_text("Employee No.: ", bold=True), _var("employee.number")),
        _paragraph(_text("Pay period: ", bold=True), _var("payroll.period")),
        _heading("Earnings", 2),
        {"type": "dynamicTable", "attrs": {"collectionPath": "earnings", "columns": [{"label": "Description", "path": "description"}, {"label": "Amount", "path": "amount", "format": "currency"}]}},
        _heading("Deductions", 2),
        {"type": "dynamicTable", "attrs": {"collectionPath": "deductions", "columns": [{"label": "Description", "path": "description"}, {"label": "Amount", "path": "amount", "format": "currency"}]}},
        _paragraph(_text("Gross pay: ", bold=True), _var("payroll.gross", "currency"), align="right"),
        _paragraph(_text("Total deductions: ", bold=True), _var("payroll.deductions", "currency"), align="right"),
        _paragraph(_text("Net pay: ", bold=True), _var("payroll.net", "currency"), align="right", border=True),
    ]


def _letter_body(spec_name: str, certificate: bool = False) -> list[Json]:
    content: list[Json] = [
        _paragraph(_text("Date: ", bold=True), _var("document.date", "date")),
        _paragraph(_var("recipient.name")),
        _paragraph(_var("recipient.address")),
        _heading(spec_name, 1, "center" if certificate else "left"),
        _paragraph(_text("Reference: ", bold=True), _var("document.reference")),
    ]
    if certificate:
        content.extend([
            _paragraph(_text("This is to certify that ", bold=True), _var("counterparty.name"), _text(" has the following confirmed account status:"), align="center"),
            _paragraph(_var("letter.body"), align="center", border=True),
            _paragraph(_text("Confirmed balance: ", bold=True), _var("totals.balanceDue", "currency"), align="center"),
        ])
    else:
        content.extend([
            _paragraph(_var("letter.salutation")),
            _paragraph(_var("letter.body"), align="justify"),
            _paragraph(_var("letter.closing")),
        ])
    return content


def _body(spec: tuple[str, str, str, str], style: Json) -> Json:
    slug, name, family, prefix = spec
    if family == "payroll":
        content = _payroll_body(style)
    elif family in {"letter", "certificate"}:
        content = _letter_body(name, family == "certificate")
    else:
        content = [
            _heading(name, 1),
            _paragraph(_text(f"{prefix} • Professional accounting document", bold=True), shading=str(style["secondaryColor"])),
            _info_table(name),
            _heading("Details", 2),
        ]
        table = _dynamic_table(family)
        if table:
            content.append(table)
        content.extend(_totals_block(family))
        content.extend([
            _heading("Notes & Approval", 2),
            _paragraph(_var("document.notes"), border=True),
            _paragraph(_text("Prepared by: ", bold=True), _var("approval.preparedBy")),
            _paragraph(_text("Approved by: ", bold=True), _var("approval.approvedBy")),
        ])
    content.extend([
        {"type": "qrCode", "attrs": {"value": "{{verification.url}}", "label": "Document verification"}},
        _paragraph(_text("Verification code: ", bold=True), _var("verification.code")),
    ])
    return {"type": "doc", "content": content}


def _header(spec_name: str) -> Json:
    return {
        "type": "doc",
        "content": [
            _paragraph(_var("company.name")),
            _paragraph(_text(spec_name.upper(), bold=True)),
            _paragraph(_var("company.registrationNumber")),
        ],
    }


def _footer(prefix: str) -> Json:
    return {
        "type": "doc",
        "content": [
            _paragraph(_var("company.address")),
            _paragraph(_var("company.phone"), _text("  •  "), _var("company.email")),
            _paragraph(_text(f"{prefix} • "), _var("document.number"), _text(" • Verify: "), _var("verification.code")),
        ],
    }


def _document(spec: tuple[str, str, str, str], style: Json, template_id: str) -> Json:
    slug, name, _family, prefix = spec
    document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{template_id}/document"))
    return {
        "schemaVersion": 1,
        "id": document_id,
        "workspaceId": "system",
        "templateId": template_id,
        "properties": {
            "title": name,
            "subject": f"Accounting / Financial — {name}",
            "author": "Ithute Document Studio",
            "category": "Accounting & Financial Documents",
            "keywords": ["accounting", "finance", slug, style["slug"]],
            "language": "en",
        },
        "settings": {
            "pageSize": "a4",
            "orientation": "portrait",
            "marginsMm": {"top": 22, "right": 18, "bottom": 20, "left": 18},
            "columns": 1,
            "headerDistanceMm": 8,
            "footerDistanceMm": 8,
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
            "documentLabel": name,
            "documentPrefix": prefix,
        },
        "header": _header(name),
        "body": _body(spec, style),
        "footer": _footer(prefix),
        "variables": {},
        "createdAt": CATALOG_TIMESTAMP,
        "updatedAt": CATALOG_TIMESTAMP,
        "version": 1,
    }


def accounting_templates() -> list[Json]:
    templates: list[Json] = []
    for spec in DOCUMENT_SPECS:
        slug, name, family, prefix = spec
        for style in STYLE_PRESETS:
            template_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"https://ithute.studio/templates/accounting/{slug}/{style['slug']}",
                )
            )
            templates.append(
                {
                    "id": template_id,
                    "workspaceId": None,
                    "name": f"{name} — {style['name']}",
                    "description": f"{style['description']} Designed for {name.lower()} workflows.",
                    "category": "finance",
                    "collection": "Accounting & Financial Documents",
                    "documentType": slug,
                    "documentTypeLabel": name,
                    "documentPrefix": prefix,
                    "family": family,
                    "stylePreset": style["slug"],
                    "styleName": style["name"],
                    "style": deepcopy(style),
                    "tags": ["accounting", "finance", slug, family, style["slug"]],
                    "isPublished": True,
                    "isBuiltIn": True,
                    "document": _document(spec, style, template_id),
                    "createdAt": CATALOG_TIMESTAMP,
                    "updatedAt": CATALOG_TIMESTAMP,
                }
            )
    return templates


_ACCOUNTING_TEMPLATES = accounting_templates()
_ACCOUNTING_BY_ID = {item["id"]: item for item in _ACCOUNTING_TEMPLATES}


def get_accounting_template(template_id: str) -> Json | None:
    item = _ACCOUNTING_BY_ID.get(template_id)
    return deepcopy(item) if item else None


def list_accounting_templates() -> list[Json]:
    return deepcopy(_ACCOUNTING_TEMPLATES)


def accounting_catalog_metadata() -> Json:
    return {
        "name": "Accounting & Financial Documents",
        "templateCount": len(_ACCOUNTING_TEMPLATES),
        "documentTypeCount": len(DOCUMENT_SPECS),
        "styleCount": len(STYLE_PRESETS),
        "styles": [deepcopy(item) for item in STYLE_PRESETS],
        "documentTypes": [
            {"slug": slug, "name": name, "family": family, "prefix": prefix}
            for slug, name, family, prefix in DOCUMENT_SPECS
        ],
    }
