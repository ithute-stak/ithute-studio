from fastapi.testclient import TestClient

from app.document_renderer import render_docx, render_pdf
from app.main import app
from app.services.institution_contract_templates import (
    INSTITUTIONS,
    institution_contract_catalog_metadata,
    list_institution_contract_templates,
)
from app.template_engine import generate_document


def _sample_contract_data() -> dict:
    return {
        "company": {
            "name": "Example Institution (Pty) Ltd",
            "address": "Maseru, Lesotho",
            "phone": "+266 0000 0000",
            "email": "contracts@example.test",
        },
        "document": {"number": "CTR-2026-000001", "date": "2026-09-18"},
        "partyA": {
            "name": "Example Institution (Pty) Ltd",
            "registrationNumber": "REG-001",
            "address": "Maseru, Lesotho",
            "signatory": "Authorised Officer",
            "signDate": "2026-09-18",
        },
        "partyB": {
            "name": "Example Client",
            "registrationNumber": "ID-001",
            "address": "Maseru, Lesotho",
            "signatory": "Client Signatory",
            "signDate": "2026-09-18",
        },
        "contract": {
            "effectiveDate": "2026-09-18",
            "product": "Professional service",
            "accountReference": "ACC-001",
            "principalOrLimit": "M 10,000",
            "pricing": "Disclosed pricing",
            "fees": "M 1,000",
            "repayment": "Monthly",
            "scope": "Provide the services described in the approved scope and schedules.",
            "paymentTerms": "Invoices are payable in accordance with the agreed payment schedule.",
            "serviceLevels": "Services are measured against the agreed service levels and acceptance criteria.",
            "partyAObligations": "Provide the contracted services, records and required notices.",
            "partyBObligations": "Provide accurate information, access and payment when due.",
            "confidentiality": "Each party must protect confidential information received under this agreement.",
            "dataProtection": "Personal information must be processed only for lawful contract purposes with appropriate safeguards.",
            "compliance": "Each party must maintain licences, permissions and records required for its obligations.",
            "termAndRenewal": "The agreement runs for the stated term and may be renewed only in writing.",
            "termination": "Material breach is subject to the applicable notice and remedy process before termination where required.",
            "liability": "Liability, insurance and indemnities remain subject to mandatory Lesotho law.",
            "disputeResolution": "The parties will first seek good-faith resolution before using an available lawful dispute process in Lesotho.",
            "notices": "Formal notices must be sent to the addresses stated by the parties.",
            "specialTerms": "Any special terms must be recorded in a signed schedule and may not override mandatory law.",
            "serviceTier": "Business",
            "support": "Business hours",
            "dataHandling": "Lesotho-controlled processing with access restrictions",
        },
        "verification": {
            "code": "VERIFY-CTR-001",
            "url": "https://verify.example.test/VERIFY-CTR-001",
        },
    }


def test_institution_contract_catalog_has_five_styles_per_contract():
    templates = list_institution_contract_templates()
    contract_types = sum(len(item["contracts"]) for item in INSTITUTIONS)
    assert len(INSTITUTIONS) == 15
    assert contract_types == 75
    assert len(templates) == 375
    assert len({item["id"] for item in templates}) == 375

    for item in templates:
        assert item["jurisdiction"] == "LS"
        assert item["family"] == "agreement"
        assert item["compliance"]["jurisdiction"] == "Kingdom of Lesotho"
        assert item["compliance"]["legalReviewRequired"] is True
        assert item["compliance"]["laws"]
        assert item["compliance"]["requiredChecks"]
        assert item["contractSchema"]["fields"]
        assert item["document"]["design"]["jurisdictionBadge"] == "LESOTHO"


def test_banking_contract_maps_current_consumer_protection_rules():
    template = next(
        item
        for item in list_institution_contract_templates()
        if item["institution"] == "contract-banking-financial"
        and item["documentType"] == "loan-facility-agreement"
        and item["stylePreset"] == "executive-navy"
    )
    titles = {law["title"] for law in template["compliance"]["laws"]}
    assert "Financial Consumer Protection Act, 2022" in titles
    assert "Financial Institutions Act, 2012" in titles
    assert "Financial Consumer Protection (Disclosure of Credit Information) Regulations, 2023" in titles
    checks = " ".join(template["compliance"]["requiredChecks"])
    assert "Key Facts Statement" in checks
    assert "cooling-off" in checks


def test_public_contract_uses_procurement_and_public_finance_profile():
    template = next(
        item
        for item in list_institution_contract_templates()
        if item["institution"] == "contract-government-public"
        and item["documentType"] == "public-works-contract"
        and item["stylePreset"] == "burgundy-gold"
    )
    titles = {law["title"] for law in template["compliance"]["laws"]}
    assert "Public Procurement Act, 2023" in titles
    assert "Public Financial Management and Accountability Act, 2011" in titles


def test_telecom_contract_uses_communications_and_data_protection_law():
    template = next(
        item
        for item in list_institution_contract_templates()
        if item["institution"] == "contract-telecom-it"
        and item["documentType"] == "saas-subscription-agreement"
        and item["stylePreset"] == "modern-teal"
    )
    titles = {law["title"] for law in template["compliance"]["laws"]}
    assert "Communications Act, 2012" in titles
    assert "Data Protection Act, 2012" in titles


def test_institution_contract_renders_backend_pdf_and_docx():
    template = next(
        item
        for item in list_institution_contract_templates()
        if item["institution"] == "contract-professional-services"
        and item["documentType"] == "consulting-services-agreement"
        and item["stylePreset"] == "executive-navy"
    )
    document = generate_document(template["document"], _sample_contract_data())
    pdf = render_pdf(document)
    docx = render_docx(document)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 4000
    assert docx.startswith(b"PK")
    assert len(docx) > 10_000


def test_contract_catalog_api_and_combined_lesotho_catalog():
    with TestClient(app) as client:
        contracts = client.get("/v1/templates/catalog/institution-contracts")
        assert contracts.status_code == 200
        payload = contracts.json()
        assert payload["institutionCount"] == 15
        assert payload["documentTypeCount"] == 75
        assert payload["templateCount"] == 375

        combined = client.get("/v1/templates/catalog/lesotho")
        assert combined.status_code == 200
        catalog = combined.json()
        assert catalog["packCount"] == 32
        assert catalog["documentTypeCount"] == 347
        assert catalog["templateCount"] == 1735

        filtered = client.get(
            "/v1/templates",
            params={
                "institution": "contract-telecom-it",
                "style": "executive-navy",
            },
        )
        assert filtered.status_code == 200
        items = filtered.json()
        assert len(items) == 5
        assert all(item["institution"] == "contract-telecom-it" for item in items)


def test_catalog_metadata_matches_generated_templates():
    metadata = institution_contract_catalog_metadata()
    assert metadata["institutionCount"] == 15
    assert metadata["documentTypeCount"] == 75
    assert metadata["styleCount"] == 5
    assert metadata["templateCount"] == 375
