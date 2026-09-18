from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.services.business_document_templates import list_business_document_templates


def _vat_template() -> dict:
    return next(
        item
        for item in list_business_document_templates()
        if item["documentType"] == "vat-invoice"
        and item["stylePreset"] == "executive-navy"
    )


def _statement_template() -> dict:
    return next(
        item
        for item in list_business_document_templates()
        if item["documentType"] == "customer-statement-of-account"
        and item["stylePreset"] == "slate-minimal"
    )


def _invoice_data() -> dict:
    return {
        "document": {
            "date": "2026-09-18",
            "dueDate": "2026-09-30",
            "currency": "LSL",
            "reference": "ORDER-001",
        },
        "items": [
            {
                "description": "Business service",
                "quantity": 2,
                "unitPrice": 1000,
                "discount": 100,
                "taxRate": 15,
            }
        ],
        "totals": {"amountPaid": 0},
    }


def test_full_document_register_workflow():
    vat = _vat_template()
    statement = _statement_template()
    with TestClient(app) as client:
        organization = client.post(
            "/v1/operations/organizations",
            json={
                "legalName": "Register Test Lesotho (Pty) Ltd",
                "tradingName": "Register Test",
                "registrationNumber": "REG-OPS-001",
                "tin": "TIN-OPS-001",
                "vatNumber": "VAT-OPS-001",
                "vatRegistered": True,
                "defaultCurrency": "LSL",
                "paymentTerms": "Payment due within 30 days.",
                "profile": {
                    "address": "Maseru, Lesotho",
                    "phone": "+266 5000 0000",
                    "email": "accounts@example.test",
                },
                "branding": {
                    "primaryColor": "#102A43",
                    "logoAssetId": "brand-logo-001",
                },
            },
        )
        assert organization.status_code == 201
        org = organization.json()

        party = client.post(
            "/v1/operations/parties",
            json={
                "organizationId": org["id"],
                "kind": "customer",
                "name": "Sample Customer (Pty) Ltd",
                "registrationNumber": "CUS-001",
                "tin": "TIN-CUS-001",
                "accountReference": "ACC-1001",
                "creditTerms": "30 days",
                "contact": {
                    "address": "Maseru",
                    "phone": "+266 5111 1111",
                    "email": "customer@example.test",
                },
            },
        )
        assert party.status_code == 201
        customer = party.json()

        rule = client.post(
            "/v1/operations/approval-rules",
            json={
                "organizationId": org["id"],
                "name": "Finance approval",
                "documentType": "vat-invoice",
                "minAmount": 1000,
                "steps": [
                    {"role": "Finance Manager"},
                    {"role": "Director"},
                ],
            },
        )
        assert rule.status_code == 201

        issue = client.post(
            "/v1/operations/documents/issue",
            json={
                "organizationId": org["id"],
                "templateId": vat["id"],
                "partyId": customer["id"],
                "documentType": "vat-invoice",
                "prefix": "VAT",
                "issuedBy": "Accounts Officer",
                "data": _invoice_data(),
            },
        )
        assert issue.status_code == 201
        document = issue.json()
        assert document["documentNumber"] == "VAT-2026-000001"
        assert document["status"] == "review"
        assert document["total"] == 2185.0
        assert document["tax"] == 285.0
        assert document["balanceDue"] == 2185.0

        approvals = client.get(
            f"/v1/operations/documents/{document['id']}/approvals"
        )
        assert approvals.status_code == 200
        steps = approvals.json()
        assert [step["role"] for step in steps] == ["Finance Manager", "Director"]

        first = client.post(
            f"/v1/operations/approvals/{steps[0]['id']}/decision",
            json={
                "status": "approved",
                "actor": "Finance Manager",
                "signature": {"type": "electronic", "name": "Finance Manager"},
            },
        )
        assert first.status_code == 200
        second = client.post(
            f"/v1/operations/approvals/{steps[1]['id']}/decision",
            json={
                "status": "approved",
                "actor": "Managing Director",
                "signature": {"type": "electronic", "name": "Managing Director"},
            },
        )
        assert second.status_code == 200
        assert second.json()["document"]["status"] == "approved"

        issued = client.post(
            f"/v1/operations/documents/{document['id']}/status",
            json={"status": "issued", "actor": "Accounts Officer"},
        )
        assert issued.status_code == 200
        assert issued.json()["issuedAt"]

        pdf = client.get(
            f"/v1/operations/documents/{document['id']}/render?format=pdf"
        )
        assert pdf.status_code == 200
        assert pdf.content.startswith(b"%PDF")
        docx = client.get(
            f"/v1/operations/documents/{document['id']}/render?format=docx"
        )
        assert docx.status_code == 200
        assert docx.content.startswith(b"PK")

        payment = client.post(
            f"/v1/operations/documents/{document['id']}/payments",
            json={
                "amount": 1000,
                "reference": "PAY-001",
                "method": "bank-transfer",
            },
        )
        assert payment.status_code == 201
        assert payment.json()["document"]["status"] == "partially-paid"
        assert payment.json()["document"]["balanceDue"] == 1185.0

        verification = client.get(
            f"/v1/operations/verify/{document['verificationCode']}"
        )
        assert verification.status_code == 200
        assert verification.json()["verified"] is True
        assert verification.json()["documentNumber"] == "VAT-2026-000001"

        delivery = client.post(
            f"/v1/operations/documents/{document['id']}/deliveries",
            json={
                "channel": "email",
                "recipient": "customer@example.test",
            },
        )
        assert delivery.status_code == 201
        sent = client.put(
            f"/v1/operations/deliveries/{delivery.json()['id']}",
            json={
                "status": "sent",
                "providerReference": "MSG-001",
            },
        )
        assert sent.status_code == 200
        assert sent.json()["sentAt"]

        statement_issue = client.post(
            "/v1/operations/documents/issue",
            json={
                "organizationId": org["id"],
                "templateId": statement["id"],
                "partyId": customer["id"],
                "documentType": "customer-statement-of-account",
                "prefix": "STM",
                "data": {
                    "document": {
                        "date": "2026-09-18",
                        "periodStart": "2026-09-01",
                        "periodEnd": "2026-09-18",
                        "currency": "LSL",
                    },
                    "summary": {"openingBalance": 0},
                    "transactions": [
                        {
                            "date": "2026-09-18",
                            "reference": document["documentNumber"],
                            "description": "Invoice",
                            "debit": 2185,
                            "credit": 1000,
                        }
                    ],
                },
                "relationParentId": document["id"],
                "relationType": "statement-for",
            },
        )
        assert statement_issue.status_code == 201
        statement_document = statement_issue.json()
        assert statement_document["documentNumber"] == "STM-2026-000001"

        relations = client.get(
            f"/v1/operations/documents/{document['id']}/relations"
        )
        assert relations.status_code == 200
        assert any(
            item["childId"] == statement_document["id"]
            and item["relationType"] == "statement-for"
            for item in relations.json()
        )

        register = client.get(
            "/v1/operations/documents",
            params={"organizationId": org["id"]},
        )
        assert register.status_code == 200
        assert len(register.json()) >= 2

        dashboard = client.get(f"/v1/operations/dashboard/{org['id']}")
        assert dashboard.status_code == 200
        summary = dashboard.json()
        assert summary["documentCount"] >= 2
        assert summary["verificationCount"] >= 1
        assert summary["amountOutstanding"] >= 1185


def test_recurring_document_issues_and_advances_schedule():
    vat = _vat_template()
    with TestClient(app) as client:
        organization = client.post(
            "/v1/operations/organizations",
            json={
                "legalName": "Recurring Test (Pty) Ltd",
                "defaultCurrency": "LSL",
            },
        ).json()
        recurring = client.post(
            "/v1/operations/recurring",
            json={
                "organizationId": organization["id"],
                "templateId": vat["id"],
                "documentType": "vat-invoice",
                "frequency": "monthly",
                "interval": 1,
                "nextRunDate": date.today().isoformat(),
                "data": _invoice_data(),
            },
        )
        assert recurring.status_code == 201
        due = client.get(
            "/v1/operations/recurring/due",
            params={"organizationId": organization["id"]},
        )
        assert due.status_code == 200
        assert any(item["id"] == recurring.json()["id"] for item in due.json())

        run = client.post(
            f"/v1/operations/recurring/{recurring.json()['id']}/run"
        )
        assert run.status_code == 200
        assert run.json()["document"]["documentNumber"].startswith("DOC-") or run.json()["document"]["documentNumber"].startswith("VAT-")
        assert run.json()["recurring"]["lastRegisterId"] == run.json()["document"]["id"]
        assert run.json()["recurring"]["nextRunDate"] > date.today().isoformat()
