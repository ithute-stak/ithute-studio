from fastapi.testclient import TestClient

from app.document_renderer import render_docx, render_pdf
from app.main import app
from app.services.accounting_engine import prepare_accounting_data
from app.services.business_document_templates import (
    PACK_SLUG,
    business_document_catalog_metadata,
    list_business_document_templates,
)
from app.template_engine import generate_document


def _business_data() -> dict:
    return {
        "company": {
            "name": "Example Lesotho (Pty) Ltd",
            "address": "Maseru, Lesotho",
            "phone": "+266 0000 0000",
            "email": "billing@example.test",
            "tin": "TIN-001",
        },
        "customer": {
            "name": "Sample Customer",
            "address": "Maseru, Lesotho",
            "phone": "+266 0000 0001",
            "email": "customer@example.test",
            "tin": "TIN-002",
            "accountNumber": "ACC-1001",
        },
        "document": {
            "number": "VAT-2026-000001",
            "date": "2026-09-18",
            "supplyDate": "2026-09-18",
            "dueDate": "2026-09-30",
            "reference": "ORDER-001",
            "purchaseOrder": "PO-001",
            "currency": "LSL",
            "terms": "Payment due by the stated due date.",
            "notes": "Thank you for your business.",
        },
        "items": [
            {
                "description": "Professional service",
                "quantity": 2,
                "unitPrice": 100,
                "discount": 10,
                "taxRate": 15,
            },
            {
                "description": "Support service",
                "quantity": 1,
                "unitPrice": 50,
                "taxRate": 15,
            },
        ],
        "totals": {"amountPaid": 50},
        "payment": {
            "method": "Bank transfer",
            "account": "0000000000",
            "reference": "VAT-2026-000001",
        },
        "statement": {
            "periodStart": "2026-09-01",
            "periodEnd": "2026-09-30",
            "openingBalance": 100,
        },
        "transactions": [
            {
                "date": "2026-09-05",
                "reference": "INV-001",
                "description": "Invoice",
                "debit": 200,
                "credit": 0,
                "balance": 300,
            },
            {
                "date": "2026-09-10",
                "reference": "PAY-001",
                "description": "Payment",
                "debit": 0,
                "credit": 50,
                "balance": 250,
            },
        ],
        "ageing": {
            "current": 250,
            "days60": 0,
            "days90": 0,
            "days90Plus": 0,
            "total": 250,
        },
        "verification": {
            "code": "VERIFY-BUSINESS-001",
            "url": "https://verify.example.test/VERIFY-BUSINESS-001",
        },
    }


def _template(document_type: str, style: str = "executive-navy") -> dict:
    return next(
        item
        for item in list_business_document_templates()
        if item["documentType"] == document_type and item["stylePreset"] == style
    )


def test_business_document_pack_has_250_templates_and_five_styles():
    catalog = business_document_catalog_metadata()
    templates = list_business_document_templates()
    assert catalog["documentTypeCount"] == 50
    assert catalog["invoiceTypeCount"] == 25
    assert catalog["statementTypeCount"] == 25
    assert catalog["styleCount"] == 5
    assert catalog["templateCount"] == 250
    assert len(templates) == 250
    assert len({item["id"] for item in templates}) == 250
    assert all(item["pack"] == PACK_SLUG for item in templates)
    assert all(item["jurisdiction"] == "LS" for item in templates)


def test_vat_invoice_has_lesotho_vat_schedule_iii_checks_and_calculates():
    template = _template("vat-invoice", "burgundy-gold")
    titles = {law["title"] for law in template["compliance"]["laws"]}
    assert "Value Added Tax Act, 2001" in titles
    checks = " ".join(template["compliance"]["requiredChecks"])
    assert "Schedule III" in checks
    assert "TINs" in checks

    data = prepare_accounting_data(template, _business_data())
    assert data["totals"]["subtotal"] == 250.0
    assert data["totals"]["discount"] == 10.0
    assert data["totals"]["tax"] == 36.0
    assert data["totals"]["total"] == 276.0
    assert data["totals"]["amountPaid"] == 50.0
    assert data["totals"]["balanceDue"] == 226.0

    document = generate_document(template["document"], data)
    pdf = render_pdf(document)
    docx = render_docx(document)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 3000
    assert docx.startswith(b"PK")
    assert len(docx) > 10_000


def test_business_statement_calculates_account_movement_and_renders():
    template = _template("customer-statement-of-account", "modern-teal")
    data = prepare_accounting_data(template, _business_data())
    assert data["statement"]["totalDebits"] == 200.0
    assert data["statement"]["totalCredits"] == 50.0
    assert data["statement"]["closingBalance"] == 250.0

    document = generate_document(template["document"], data)
    pdf = render_pdf(document)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 3000


def test_business_catalog_and_accounting_preview_api_accept_new_templates():
    template = _template("business-invoice")
    with TestClient(app) as client:
        catalog = client.get("/v1/templates/catalog/business-documents")
        assert catalog.status_code == 200
        payload = catalog.json()
        assert payload["templateCount"] == 250
        assert payload["invoiceTypeCount"] == 25
        assert payload["statementTypeCount"] == 25

        pack = client.get(
            "/v1/templates",
            params={"pack": PACK_SLUG, "style": "executive-navy"},
        )
        assert pack.status_code == 200
        assert len(pack.json()) == 50

        preview = client.post(
            "/v1/accounting/preview",
            json={"templateId": template["id"], "data": _business_data()},
        )
        assert preview.status_code == 200
        preview_data = preview.json()["data"]
        assert preview_data["totals"]["total"] == 276.0
        assert preview.json()["form"]["collectionPath"] == "items"
