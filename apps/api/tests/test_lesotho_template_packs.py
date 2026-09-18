from fastapi.testclient import TestClient

from app.document_renderer import render_docx, render_pdf
from app.main import app
from app.services.lesotho_template_packs import (
    LAW_PROFILE_VERSION,
    PACKS,
    list_lesotho_templates,
)
from app.template_engine import generate_document


def _sample_data() -> dict:
    return {
        "company": {
            "name": "Example Lesotho (Pty) Ltd",
            "address": "Maseru, Lesotho",
            "phone": "+266 0000 0000",
            "email": "info@example.test",
        },
        "document": {
            "number": "LS-2026-000001",
            "date": "2026-09-18",
            "reference": "REF-001",
            "subject": "Sample subject",
            "purpose": "Sample purpose",
            "terms": "Sample terms for testing backend rendering.",
            "body": "Sample body for testing backend rendering.",
            "notes": "Sample notes.",
            "declaration": "I confirm the information supplied is correct.",
        },
        "recipient": {"name": "Sample Recipient", "address": "Maseru"},
        "subject": {"name": "Sample Subject", "identifier": "ID-001", "contact": "+266 0000 0000"},
        "partyA": {"name": "Example Lesotho (Pty) Ltd"},
        "partyB": {"name": "Sample Counterparty"},
        "signatory": {"name": "Authorised Signatory", "date": "2026-09-18"},
        "verification": {"code": "VERIFY-001", "url": "https://verify.example.test/VERIFY-001"},
        "employment": {
            "type": "Indefinite",
            "startDate": "2026-09-18",
            "jobTitle": "Business Manager",
            "workplace": "Maseru",
            "remuneration": "M 4,500 monthly",
            "hours": "As lawfully agreed",
            "probation": "Four months",
            "leave": "Statutory minimums or better",
            "termination": "Subject to Labour Act 2024",
        },
        "credit": {
            "principal": "M 10,000",
            "interest": "Disclosed annual rate",
            "fees": "Disclosed fees",
            "totalCost": "M 11,500",
            "repayment": "12 monthly instalments",
            "defaultTerms": "As disclosed and permitted by law",
            "complaints": "Internal complaints unit / CBL",
            "kfsAcknowledgement": "Acknowledged",
            "amountOverdue": "M 1,000",
            "remedy": "Pay the overdue amount or contact the provider to discuss lawful remedial options.",
            "consumerRights": "Consumer rights and complaint channels have been disclosed.",
        },
    }


def test_all_requested_packs_have_five_styles_and_lesotho_profile():
    templates = list_lesotho_templates()
    document_types = sum(len(pack["documents"]) for pack in PACKS)
    assert len(PACKS) == 16
    assert document_types == 222
    assert len(templates) == 1110
    assert len({item["id"] for item in templates}) == 1110

    for item in templates:
        compliance = item["compliance"]
        assert compliance["jurisdiction"] == "Kingdom of Lesotho"
        assert compliance["profileVersion"] == LAW_PROFILE_VERSION
        assert compliance["verifiedAt"] == "2026-09-18"
        assert compliance["laws"]
        assert compliance["requiredChecks"]
        assert item["document"]["header"]["content"]
        assert item["document"]["footer"]["content"]
        assert item["document"]["design"]["jurisdictionBadge"] == "LESOTHO"


def test_hr_contract_uses_current_labour_act_profile():
    template = next(
        item
        for item in list_lesotho_templates()
        if item["pack"] == "hr-employment"
        and item["documentType"] == "employment-contract"
        and item["stylePreset"] == "burgundy-gold"
    )
    titles = {law["title"] for law in template["compliance"]["laws"]}
    assert "Labour Act, 2024" in titles
    assert "Data Protection Act, 2012" in titles
    checks = " ".join(template["compliance"]["requiredChecks"])
    assert "four months" in checks
    assert "written notice" in checks
    assert template["compliance"]["legalReviewRequired"] is True


def test_lending_templates_include_consumer_credit_protection_rules():
    template = next(
        item
        for item in list_lesotho_templates()
        if item["pack"] == "lending-credit"
        and item["documentType"] == "arrears-notice"
        and item["stylePreset"] == "executive-navy"
    )
    titles = {law["title"] for law in template["compliance"]["laws"]}
    assert "Financial Consumer Protection Act, 2022" in titles
    assert "Financial Consumer Protection (Disclosure of Credit Information) Regulations, 2023" in titles
    assert "Credit Reporting Act, 2011" in titles
    checks = " ".join(template["compliance"]["requiredChecks"])
    assert "written default notice" in checks
    assert "overdue amount" in checks


def test_lesotho_template_renders_backend_pdf_and_docx():
    template = next(
        item
        for item in list_lesotho_templates()
        if item["pack"] == "hr-employment"
        and item["documentType"] == "employment-contract"
        and item["stylePreset"] == "executive-navy"
    )
    document = generate_document(template["document"], _sample_data())
    pdf = render_pdf(document)
    docx = render_docx(document)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 2500
    assert docx.startswith(b"PK")
    assert len(docx) > 10_000


def test_lesotho_catalog_api_and_pack_filter():
    with TestClient(app) as client:
        catalog = client.get("/v1/templates/catalog/lesotho")
        assert catalog.status_code == 200
        payload = catalog.json()
        assert payload["packCount"] == 31
        assert payload["documentTypeCount"] == 297
        assert payload["templateCount"] == 1485
        assert payload["jurisdiction"] == "Kingdom of Lesotho"

        templates = client.get(
            "/v1/templates",
            params={"pack": "lending-credit", "style": "executive-navy"},
        )
        assert templates.status_code == 200
        items = [item for item in templates.json() if item.get("isBuiltIn")]
        assert len(items) == 18
        assert all(item["jurisdiction"] == "LS" for item in items)
