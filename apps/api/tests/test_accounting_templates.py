from fastapi.testclient import TestClient

from app.document_renderer import render_docx, render_pdf
from app.main import app
from app.services.accounting_templates import (
    DOCUMENT_SPECS,
    STYLE_PRESETS,
    list_accounting_templates,
)
from app.template_engine import generate_document


def _sample_accounting_data() -> dict:
    return {
        "company": {
            "name": "Example Holdings (Pty) Ltd",
            "registrationNumber": "REG-2026-001",
            "address": "Maseru, Lesotho",
            "phone": "+266 0000 0000",
            "email": "accounts@example.test",
        },
        "counterparty": {"name": "Sample Customer"},
        "recipient": {"name": "Sample Customer", "address": "Maseru"},
        "document": {
            "number": "INV-2026-000001",
            "reference": "ORDER-77",
            "date": "2026-09-18",
            "currency": "LSL",
            "notes": "Thank you for your business.",
        },
        "items": [
            {
                "description": "Professional services",
                "quantity": 2,
                "unitPrice": 750,
                "tax": 225,
                "total": 1725,
            },
            {
                "description": "Administration",
                "quantity": 1,
                "unitPrice": 250,
                "tax": 37.5,
                "total": 287.5,
            },
        ],
        "totals": {
            "subtotal": 1750,
            "tax": 262.5,
            "total": 2012.5,
            "balanceDue": 2012.5,
        },
        "verification": {
            "code": "ITH-ACC-000001",
            "url": "https://verify.example.test/ITH-ACC-000001",
        },
        "approval": {"preparedBy": "Finance Office", "approvedBy": "Finance Manager"},
    }


def test_accounting_catalog_has_five_styles_for_every_document_type():
    templates = list_accounting_templates()
    assert len(DOCUMENT_SPECS) == 41
    assert len(STYLE_PRESETS) == 5
    assert len(templates) == 205
    assert len({item["id"] for item in templates}) == 205

    for slug, _name, _family, _prefix in DOCUMENT_SPECS:
        variants = [item for item in templates if item["documentType"] == slug]
        assert len(variants) == 5
        assert {item["stylePreset"] for item in variants} == {
            style["slug"] for style in STYLE_PRESETS
        }
        for item in variants:
            document = item["document"]
            assert document["header"]["content"]
            assert document["footer"]["content"]
            assert document["design"]["primaryColor"].startswith("#")
            assert document["design"]["headerStyle"]
            assert document["design"]["footerStyle"]


def test_accounting_invoice_renders_styled_backend_pdf_and_docx():
    template = next(
        item
        for item in list_accounting_templates()
        if item["documentType"] == "invoice"
        and item["stylePreset"] == "burgundy-gold"
    )
    document = generate_document(template["document"], _sample_accounting_data())
    pdf = render_pdf(document)
    docx = render_docx(document)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 2500
    assert docx.startswith(b"PK")
    assert len(docx) > 10_000


def test_accounting_catalog_api_and_builtin_template_lookup():
    with TestClient(app) as client:
        metadata = client.get("/v1/templates/catalog/accounting")
        assert metadata.status_code == 200
        assert metadata.json()["templateCount"] == 205
        assert metadata.json()["documentTypeCount"] == 41
        assert metadata.json()["styleCount"] == 5

        templates = client.get(
            "/v1/templates",
            params={
                "category": "finance",
                "document_type": "invoice",
                "style": "executive-navy",
            },
        )
        assert templates.status_code == 200
        built_ins = [item for item in templates.json() if item.get("isBuiltIn")]
        assert len(built_ins) == 1
        chosen = built_ins[0]

        fetched = client.get(f"/v1/templates/{chosen['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["name"] == chosen["name"]
        assert fetched.json()["document"]["design"]["preset"] == "executive-navy"
