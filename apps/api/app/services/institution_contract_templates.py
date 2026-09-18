from __future__ import annotations

import re
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

EXTRA_LAW_SOURCES: dict[str, Json] = {
    "communications-2012": {
        "title": "Communications Act, 2012",
        "citation": "Act 4 of 2012",
        "authority": "Kingdom of Lesotho / Lesotho Communications Authority",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2012/4/eng@2012-02-17",
    }
}

INSTITUTIONS: tuple[Json, ...] = (
    {
        "slug": "contract-banking-financial",
        "name": "Banks & Financial Institutions",
        "category": "contracts",
        "laws": [
            "financial-institutions-2012",
            "financial-consumer-2022",
            "financial-disclosure-2023",
            "credit-reporting-2011",
            "data-protection-2012",
            "aml-2008",
            "aml-regs-2019",
        ],
        "checks": [
            "Confirm the institution is licensed or authorised for the product or service covered by the agreement.",
            "Provide material terms in clear, fair and intelligible language and provide the applicable Key Facts Statement before the consumer is bound.",
            "Disclose interest, fees, charges, total cost, repayment/payment terms, default consequences and complaint channels before signature.",
            "Do not change agreed contract terms or impose undisclosed charges except as permitted by law and the contract.",
            "Apply the statutory cooling-off/cancellation right where the Financial Consumer Protection Act makes it applicable.",
        ],
        "scheduleFields": [
            ("Product / facility", "contract.product"),
            ("Account / facility reference", "contract.accountReference"),
            ("Principal / limit", "contract.principalOrLimit"),
            ("Interest / pricing", "contract.pricing"),
            ("Fees / charges", "contract.fees"),
            ("Repayment / payment schedule", "contract.repayment"),
        ],
        "contracts": [
            "Bank Account Services Agreement",
            "Loan Facility Agreement",
            "Overdraft Facility Agreement",
            "Merchant Services Agreement",
            "Financial Services Client Agreement",
        ],
    },
    {
        "slug": "contract-microfinance-credit",
        "name": "Microfinance & Credit Providers",
        "category": "contracts",
        "laws": [
            "financial-consumer-2022",
            "financial-disclosure-2023",
            "credit-reporting-2011",
            "money-lenders",
            "data-protection-2012",
            "aml-2008",
        ],
        "checks": [
            "Confirm the credit provider holds every licence or registration required for the credit activity.",
            "Use a Key Facts Statement and disclose total credit cost, interest, fees, instalments and default consequences before execution.",
            "Any salary-deduction authority must be specific, voluntary where required, accurately identify the debt and not override statutory protections.",
            "Before enforcement, issue the notices and remedy information required by financial consumer-protection law.",
        ],
        "scheduleFields": [
            ("Credit amount", "contract.principalOrLimit"),
            ("Interest / pricing", "contract.pricing"),
            ("Fees", "contract.fees"),
            ("Instalment", "contract.instalment"),
            ("Repayment frequency", "contract.repayment"),
            ("Security / guarantor", "contract.security"),
        ],
        "contracts": [
            "Microloan Agreement",
            "Salary Deduction Agreement",
            "Guarantor Agreement",
            "Debt Restructuring Agreement",
            "Credit Provider Service Agreement",
        ],
    },
    {
        "slug": "contract-insurance",
        "name": "Insurance Institutions",
        "category": "contracts",
        "laws": [
            "insurance-2014",
            "insurance-codes-2016",
            "financial-consumer-2022",
            "data-protection-2012",
        ],
        "checks": [
            "Confirm insurer/intermediary licensing and authority for the class of insurance or service.",
            "State cover, exclusions, premium, excess, claims process, cancellation and complaint routes clearly.",
            "Do not represent a service agreement as a policy or proof of cover unless the authorised insurer has actually issued the policy/cover.",
        ],
        "scheduleFields": [
            ("Policy / programme", "contract.product"),
            ("Class of insurance", "contract.insuranceClass"),
            ("Premium / fee", "contract.fees"),
            ("Cover period", "contract.term"),
            ("Excess / deductible", "contract.excess"),
            ("Claims contact", "contract.claimsContact"),
        ],
        "contracts": [
            "Insurance Services Agreement",
            "Broker Appointment Agreement",
            "Group Insurance Agreement",
            "Claims Administration Agreement",
            "Insurance Premium Collection Agreement",
        ],
    },
    {
        "slug": "contract-education",
        "name": "Schools & Education Institutions",
        "category": "contracts",
        "laws": ["education-2010", "data-protection-2012", "labour-2024"],
        "checks": [
            "Confirm the school or education provider has the registration/authority required for the service offered.",
            "State fees, refund rules, term dates, service scope, discipline/boarding/transport conditions and parent/guardian obligations clearly.",
            "Protect learner information, especially information about children, in accordance with data-protection requirements.",
        ],
        "scheduleFields": [
            ("Learner / student", "contract.studentName"),
            ("Academic year / term", "contract.academicPeriod"),
            ("Programme / grade", "contract.programme"),
            ("Fees", "contract.fees"),
            ("Payment schedule", "contract.repayment"),
            ("Parent / guardian", "contract.guardian"),
        ],
        "contracts": [
            "Student Enrolment and Fee Agreement",
            "Boarding and Hostel Agreement",
            "School Transport Agreement",
            "Education Service Provider Agreement",
            "School Supplier Agreement",
        ],
    },
    {
        "slug": "contract-healthcare",
        "name": "Clinics & Healthcare Institutions",
        "category": "contracts",
        "laws": ["public-health-1970", "data-protection-2012", "companies-2011"],
        "checks": [
            "Confirm that clinical services are delivered and authorised by appropriately qualified/licensed personnel where required.",
            "Health information is sensitive; define lawful collection, access, retention, sharing and confidentiality controls.",
            "Do not use contractual wording to waive non-waivable patient rights or replace informed clinical consent where separate consent is required.",
        ],
        "scheduleFields": [
            ("Service / programme", "contract.product"),
            ("Patient / client reference", "contract.accountReference"),
            ("Service fee", "contract.fees"),
            ("Service location", "contract.location"),
            ("Responsible practitioner / unit", "contract.responsibleUnit"),
            ("Health-data handling", "contract.dataHandling"),
        ],
        "contracts": [
            "Patient Services Agreement",
            "Medical Services Provider Agreement",
            "Clinic Corporate Services Agreement",
            "Medical Equipment Service Agreement",
            "Health Data Processing Agreement",
        ],
    },
    {
        "slug": "contract-ngo-development",
        "name": "NGOs & Development Institutions",
        "category": "contracts",
        "laws": ["companies-2011", "data-protection-2012", "aml-2008"],
        "checks": [
            "Confirm the legal status, signing authority, donor restrictions and approved purpose of funds or programme resources.",
            "Define outputs, eligible expenditure, reporting, audit, anti-fraud, safeguarding and recovery/suspension rights.",
            "Beneficiary and donor information must be processed lawfully and only for legitimate programme purposes.",
        ],
        "scheduleFields": [
            ("Programme / project", "contract.project"),
            ("Grant / funding amount", "contract.principalOrLimit"),
            ("Funding period", "contract.term"),
            ("Deliverables", "contract.deliverables"),
            ("Reporting schedule", "contract.reporting"),
            ("Budget / eligible costs", "contract.budget"),
        ],
        "contracts": [
            "Grant Agreement",
            "Donor Funding Agreement",
            "Implementing Partner Agreement",
            "Beneficiary Support Agreement",
            "Volunteer Service Agreement",
        ],
    },
    {
        "slug": "contract-construction-engineering",
        "name": "Construction & Engineering Institutions",
        "category": "contracts",
        "laws": [
            "building-control-1995",
            "environment-2008",
            "labour-2024",
            "data-protection-2012",
        ],
        "checks": [
            "Confirm permits, approved drawings, project authority and competent professional appointments required for the works.",
            "Define scope/BOQ, price, variations, programme, defects, safety, insurance, payment certification and handover clearly.",
            "Environmental and labour obligations remain mandatory even where the contract allocates responsibility between parties.",
        ],
        "scheduleFields": [
            ("Project", "contract.project"),
            ("Site", "contract.location"),
            ("Contract sum / rate", "contract.fees"),
            ("Programme / completion date", "contract.term"),
            ("BOQ / scope reference", "contract.scopeReference"),
            ("Retention / defects period", "contract.retention"),
        ],
        "contracts": [
            "Construction Works Agreement",
            "Subcontractor Agreement",
            "Equipment Hire Agreement",
            "Materials Supply Agreement",
            "Engineering Consultancy Agreement",
        ],
    },
    {
        "slug": "contract-property-facilities",
        "name": "Property & Facilities Institutions",
        "category": "contracts",
        "laws": ["land-2010", "land-regs-2011", "building-control-1995", "data-protection-2012"],
        "checks": [
            "Verify the lessor/owner/manager's legal right to deal with the property and record the correct plot, lease or title identifiers.",
            "Identify transactions requiring Commissioner consent, registration or prescribed land documentation before treating the transaction as complete.",
            "State rent/fees, deposit, use, maintenance, access, utilities, renewal and termination obligations clearly.",
        ],
        "scheduleFields": [
            ("Property / premises", "contract.property"),
            ("Plot / lease / title no.", "contract.titleNumber"),
            ("Location", "contract.location"),
            ("Rent / service fee", "contract.fees"),
            ("Deposit", "contract.deposit"),
            ("Term", "contract.term"),
        ],
        "contracts": [
            "Residential Lease Agreement",
            "Commercial Lease Agreement",
            "Property Management Agreement",
            "Facilities Maintenance Agreement",
            "Property Service Contractor Agreement",
        ],
    },
    {
        "slug": "contract-transport-logistics",
        "name": "Transport & Logistics Institutions",
        "category": "contracts",
        "laws": ["road-traffic-1981", "road-regs-1981", "labour-2024", "data-protection-2012"],
        "checks": [
            "Confirm vehicle licensing, roadworthiness, driver licensing and any permit/operating authority required for the service.",
            "Define load/passenger responsibility, delivery conditions, fuel/mileage, damage, insurance and accident reporting obligations.",
            "Contract terms must not authorise unsafe operation or override road-traffic and employment requirements.",
        ],
        "scheduleFields": [
            ("Vehicle / fleet", "contract.vehicle"),
            ("Registration no.", "contract.registrationNumber"),
            ("Route / service area", "contract.route"),
            ("Rate / hire fee", "contract.fees"),
            ("Mileage / usage basis", "contract.usageBasis"),
            ("Insurance reference", "contract.insuranceReference"),
        ],
        "contracts": [
            "Vehicle Hire Agreement",
            "Goods Transport Agreement",
            "Courier Services Agreement",
            "Fleet Maintenance Agreement",
            "Driver and Operator Services Agreement",
        ],
    },
    {
        "slug": "contract-telecom-it",
        "name": "Telecommunications & IT Institutions",
        "category": "contracts",
        "laws": ["communications-2012", "data-protection-2012", "companies-2011"],
        "checks": [
            "Confirm any communications licence/authorisation required for the service and do not include anti-competitive restrictions prohibited by communications law.",
            "Define availability/SLA, support, security, backups, incident handling, ownership/licensing of IP and exit/data-return obligations.",
            "Where one party processes personal data for another, allocate controller/processor obligations and security/confidentiality responsibilities clearly.",
        ],
        "scheduleFields": [
            ("System / service", "contract.product"),
            ("Hosting / service tier", "contract.serviceTier"),
            ("Monthly / project fee", "contract.fees"),
            ("SLA / availability", "contract.serviceLevels"),
            ("Support hours", "contract.support"),
            ("Data location / handling", "contract.dataHandling"),
        ],
        "contracts": [
            "Software Development Agreement",
            "SaaS Subscription Agreement",
            "Website Hosting Agreement",
            "IT Support and Maintenance Agreement",
            "Data Processing Agreement",
        ],
    },
    {
        "slug": "contract-retail-distribution",
        "name": "Retail, Trade & Distribution Institutions",
        "category": "contracts",
        "laws": ["companies-2011", "vat-2001", "data-protection-2012"],
        "checks": [
            "Confirm legal business names, authority, product specifications, pricing/tax treatment and delivery/acceptance terms.",
            "Define title/risk transfer, defective goods, returns, warranties, stock reconciliation and payment/default provisions.",
            "Do not use distribution restrictions that are unlawful or beyond the parties' legitimate commercial rights.",
        ],
        "scheduleFields": [
            ("Goods / equipment", "contract.product"),
            ("Territory / outlet", "contract.location"),
            ("Price / discount", "contract.fees"),
            ("Minimum order / volume", "contract.volume"),
            ("Delivery terms", "contract.delivery"),
            ("Warranty / returns", "contract.warranty"),
        ],
        "contracts": [
            "Goods Supply Agreement",
            "Distribution Agreement",
            "Consignment Agreement",
            "Wholesale Supply Agreement",
            "Equipment Sale and Maintenance Agreement",
        ],
    },
    {
        "slug": "contract-professional-services",
        "name": "Professional Service Institutions",
        "category": "contracts",
        "laws": ["companies-2011", "data-protection-2012", "labour-2024"],
        "checks": [
            "Confirm professional registration/licensing where the service is regulated and identify the authorised service provider.",
            "Define scope, deliverables, professional standard, fees, expenses, client dependencies, confidentiality and ownership of work product.",
            "An independent-contractor label must not be used to disguise an employment relationship where the facts create one under labour law.",
        ],
        "scheduleFields": [
            ("Engagement", "contract.project"),
            ("Scope", "contract.scopeReference"),
            ("Fee / retainer", "contract.fees"),
            ("Deliverables", "contract.deliverables"),
            ("Reporting / review", "contract.reporting"),
            ("Professional registration", "contract.licenceReference"),
        ],
        "contracts": [
            "Consulting Services Agreement",
            "Accounting and Bookkeeping Agreement",
            "Marketing Agency Agreement",
            "Retainer Services Agreement",
            "Training Services Agreement",
        ],
    },
    {
        "slug": "contract-government-public",
        "name": "Government & Public Institutions",
        "category": "contracts",
        "laws": ["procurement-2023", "pfma-2011", "data-protection-2012"],
        "checks": [
            "Use the procurement method, approvals, solicitation documents, award authority and contract conditions required by the Public Procurement Act 2023 and applicable instruments.",
            "Preserve value-for-money, audit, anti-corruption, records, performance-security and public-financial-management requirements.",
            "The Studio template does not replace prescribed tender/contract conditions issued by the procuring entity or competent authority.",
        ],
        "scheduleFields": [
            ("Procuring entity", "contract.procuringEntity"),
            ("Procurement reference", "contract.procurementReference"),
            ("Contract / framework value", "contract.fees"),
            ("Delivery / completion period", "contract.term"),
            ("Performance security", "contract.security"),
            ("Contract manager", "contract.responsibleUnit"),
        ],
        "contracts": [
            "Public Works Contract",
            "Government Goods Supply Contract",
            "Non-Consultancy Services Contract",
            "Consultancy Services Contract",
            "Framework Agreement",
        ],
    },
    {
        "slug": "contract-security-services",
        "name": "Security Service Institutions",
        "category": "contracts",
        "laws": ["companies-2011", "labour-2024", "data-protection-2012"],
        "checks": [
            "Confirm every licence, registration, firearm/controlled-equipment authority or other sector permission required for the actual security service before issue.",
            "Define posts/sites, staffing, shifts, incident escalation, access control, confidentiality, liability, insurance and performance reporting.",
            "CCTV/access-control data must be processed lawfully and access to recordings/logs must be restricted.",
        ],
        "scheduleFields": [
            ("Site / premises", "contract.location"),
            ("Security service", "contract.product"),
            ("Posts / staffing", "contract.staffing"),
            ("Hours / shifts", "contract.serviceLevels"),
            ("Monthly / project fee", "contract.fees"),
            ("Incident escalation", "contract.incidentEscalation"),
        ],
        "contracts": [
            "Guarding Services Agreement",
            "Alarm Monitoring Agreement",
            "CCTV Installation and Maintenance Agreement",
            "Security Systems Maintenance Agreement",
            "Access Control Services Agreement",
        ],
    },
    {
        "slug": "contract-hospitality-events",
        "name": "Hospitality & Events Institutions",
        "category": "contracts",
        "laws": ["companies-2011", "vat-2001", "data-protection-2012"],
        "checks": [
            "State booking/service dates, capacity, fees/taxes, deposit, cancellation/refund terms, damage responsibility and service inclusions clearly.",
            "Protect guest, attendee and client personal information and payment/contact records.",
            "Confirm any venue, food-service, entertainment, liquor or event permissions separately where the activity requires them.",
        ],
        "scheduleFields": [
            ("Venue / property", "contract.location"),
            ("Event / service", "contract.project"),
            ("Event / stay dates", "contract.term"),
            ("Guests / attendees", "contract.capacity"),
            ("Fee / package", "contract.fees"),
            ("Deposit / cancellation", "contract.deposit"),
        ],
        "contracts": [
            "Venue Hire Agreement",
            "Catering Services Agreement",
            "Corporate Accommodation Agreement",
            "Event Services Agreement",
            "Conference Services Agreement",
        ],
    },
)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _text(value: str, *, bold: bool = False) -> Json:
    node: Json = {"type": "text", "text": value}
    if bold:
        node["marks"] = [{"type": "bold"}]
    return node


def _var(path: str) -> Json:
    return {"type": "variable", "attrs": {"path": path}}


def _p(*nodes: Json, border: bool = False, align: str = "left") -> Json:
    return {
        "type": "paragraph",
        "attrs": {"textAlign": align, **({"border": True} if border else {})},
        "content": list(nodes),
    }


def _h(value: str, level: int = 1) -> Json:
    return {"type": "heading", "attrs": {"level": level}, "content": [_text(value)]}


def _law_source(key: str) -> Json:
    source = EXTRA_LAW_SOURCES.get(key) or LAW_SOURCES.get(key)
    if source is None:
        raise KeyError(f"Unknown law source: {key}")
    return deepcopy(source)


def _signature_table() -> Json:
    return {
        "type": "table",
        "content": [
            {
                "type": "tableRow",
                "content": [
                    {
                        "type": "tableCell",
                        "content": [
                            _p(_text("For Party A", bold=True)),
                            _p(_var("partyA.signatory")),
                            _p(_var("partyA.signDate")),
                        ],
                    },
                    {
                        "type": "tableCell",
                        "content": [
                            _p(_text("For Party B", bold=True)),
                            _p(_var("partyB.signatory")),
                            _p(_var("partyB.signDate")),
                        ],
                    },
                ],
            }
        ],
    }


def _body(institution: Json, contract_name: str) -> Json:
    content: list[Json] = [
        _h(contract_name),
        _p(_text("KINGDOM OF LESOTHO • INSTITUTION CONTRACT", bold=True)),
        _p(_text("Agreement reference: ", bold=True), _var("document.number")),
        _p(_text("Effective date: ", bold=True), _var("contract.effectiveDate")),
        _h("1. Parties and authority", 2),
        _p(_text("Party A: ", bold=True), _var("partyA.name")),
        _p(_text("Registration / ID: ", bold=True), _var("partyA.registrationNumber")),
        _p(_text("Address: ", bold=True), _var("partyA.address")),
        _p(_text("Party B: ", bold=True), _var("partyB.name")),
        _p(_text("Registration / ID: ", bold=True), _var("partyB.registrationNumber")),
        _p(_text("Address: ", bold=True), _var("partyB.address")),
        _p(_text("Each signatory confirms that they have authority and legal capacity to bind the party they represent.")),
        _h("2. Contract particulars", 2),
    ]
    for label, path in institution["scheduleFields"]:
        content.append(_p(_text(f"{label}: ", bold=True), _var(path)))
    content.extend(
        [
            _h("3. Purpose and scope", 2),
            _p(_var("contract.scope"), border=True),
            _h("4. Price, fees and payment", 2),
            _p(_var("contract.paymentTerms"), border=True),
            _h("5. Service levels, delivery and acceptance", 2),
            _p(_var("contract.serviceLevels"), border=True),
            _h("6. Party A obligations", 2),
            _p(_var("contract.partyAObligations"), border=True),
            _h("7. Party B obligations", 2),
            _p(_var("contract.partyBObligations"), border=True),
            _h("8. Confidentiality and data protection", 2),
            _p(_var("contract.confidentiality"), border=True),
            _p(_var("contract.dataProtection"), border=True),
            _h("9. Compliance, licences and records", 2),
            _p(_var("contract.compliance"), border=True),
            _h("10. Term, renewal and variation", 2),
            _p(_var("contract.termAndRenewal"), border=True),
            _h("11. Default, remedies and termination", 2),
            _p(_var("contract.termination"), border=True),
            _h("12. Liability, insurance and indemnities", 2),
            _p(_var("contract.liability"), border=True),
            _h("13. Dispute resolution and governing law", 2),
            _p(_var("contract.disputeResolution"), border=True),
            _p(
                _text(
                    "This agreement is governed by the laws of the Kingdom of Lesotho, subject to mandatory statutory and regulatory requirements applicable to the institution, service and transaction."
                )
            ),
            _h("14. Notices", 2),
            _p(_var("contract.notices"), border=True),
            _h("15. Special terms and schedules", 2),
            _p(_var("contract.specialTerms"), border=True),
            _h("Lesotho compliance checklist", 2),
        ]
    )
    content.extend(_p(_text(f"• {check}")) for check in institution["checks"])
    content.extend(
        [
            _p(_text("Compliance profile: ", bold=True), _text(LAW_PROFILE_VERSION)),
            _p(
                _text(
                    "Legal review required before execution. The template does not replace prescribed forms, regulator approvals, licences, registrations, notarisation, witnessing or transaction-specific legal advice."
                ),
                border=True,
            ),
            _h("Execution", 2),
            _signature_table(),
        ]
    )
    return {"type": "doc", "content": content}


def _header(institution_name: str, contract_name: str) -> Json:
    return {
        "type": "doc",
        "content": [
            _p(_var("company.name")),
            _p(_text(institution_name.upper(), bold=True)),
            _p(_text(contract_name, bold=True)),
        ],
    }


def _footer(institution_name: str) -> Json:
    return {
        "type": "doc",
        "content": [
            _p(
                _text("Kingdom of Lesotho • "),
                _text(institution_name),
                _text(" • Contract profile "),
                _text(LAW_PROFILE_VERSION),
            ),
            _p(
                _var("company.address"),
                _text(" • "),
                _var("company.phone"),
                _text(" • "),
                _var("company.email"),
            ),
            _p(
                _text("Agreement "),
                _var("document.number"),
                _text(" • Verify "),
                _var("verification.code"),
            ),
        ],
    }


def _template(institution: Json, contract_name: str, style: Json) -> Json:
    contract_slug = _slug(contract_name)
    template_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"https://ithute.studio/templates/lesotho/contracts/{institution['slug']}/{contract_slug}/{style['slug']}",
        )
    )
    document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{template_id}/document"))
    laws = [_law_source(key) for key in institution["laws"]]
    compliance = {
        "jurisdiction": "Kingdom of Lesotho",
        "profileVersion": LAW_PROFILE_VERSION,
        "verifiedAt": "2026-09-18",
        "riskLevel": "high",
        "legalReviewRequired": True,
        "laws": laws,
        "requiredChecks": deepcopy(institution["checks"]),
        "note": "Institution-contract compliance profile. Validate licences, prescribed forms, approvals, execution formalities and transaction facts before signature.",
    }
    fields = [
        {"label": label, "path": path, "required": True}
        for label, path in institution["scheduleFields"]
    ]
    fields.extend(
        [
            {"label": "Scope", "path": "contract.scope", "required": True},
            {"label": "Payment terms", "path": "contract.paymentTerms", "required": True},
            {"label": "Term and renewal", "path": "contract.termAndRenewal", "required": True},
            {"label": "Termination", "path": "contract.termination", "required": True},
            {"label": "Dispute resolution", "path": "contract.disputeResolution", "required": True},
        ]
    )
    document = {
        "schemaVersion": 1,
        "id": document_id,
        "workspaceId": "system",
        "templateId": template_id,
        "properties": {
            "title": contract_name,
            "subject": f"{institution['name']} — {contract_name}",
            "author": "Ithute Document Studio",
            "category": "Institution Contracts",
            "keywords": [
                "Lesotho",
                "contract",
                institution["slug"],
                contract_slug,
                style["slug"],
            ],
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
            "pageNumbering": {
                "enabled": True,
                "startAt": 1,
                "format": "1",
                "position": "footer",
            },
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
            "documentLabel": contract_name,
            "jurisdictionBadge": "LESOTHO",
        },
        "compliance": compliance,
        "contractSchema": {
            "institution": institution["name"],
            "legalReviewRequired": True,
            "fields": fields,
        },
        "header": _header(str(institution["name"]), contract_name),
        "body": _body(institution, contract_name),
        "footer": _footer(str(institution["name"])),
        "variables": {},
        "createdAt": CATALOG_TIMESTAMP,
        "updatedAt": CATALOG_TIMESTAMP,
        "version": 1,
    }
    return {
        "id": template_id,
        "workspaceId": None,
        "name": f"{contract_name} — {style['name']}",
        "description": (
            f"Lesotho law-aware {contract_name.lower()} for {institution['name'].lower()}, "
            f"with {style['name']} styling and institution-specific contract schedules."
        ),
        "category": institution["category"],
        "collection": institution["name"],
        "pack": institution["slug"],
        "institution": institution["slug"],
        "institutionLabel": institution["name"],
        "documentType": contract_slug,
        "documentTypeLabel": contract_name,
        "family": "agreement",
        "stylePreset": style["slug"],
        "styleName": style["name"],
        "style": deepcopy(style),
        "jurisdiction": "LS",
        "compliance": compliance,
        "contractSchema": deepcopy(document["contractSchema"]),
        "tags": [
            "Lesotho",
            "contract",
            institution["slug"],
            contract_slug,
            style["slug"],
        ],
        "isPublished": True,
        "isBuiltIn": True,
        "document": document,
        "createdAt": CATALOG_TIMESTAMP,
        "updatedAt": CATALOG_TIMESTAMP,
    }


def institution_contract_templates() -> list[Json]:
    return [
        _template(institution, contract_name, style)
        for institution in INSTITUTIONS
        for contract_name in institution["contracts"]
        for style in STYLE_PRESETS
    ]


_INSTITUTION_CONTRACT_TEMPLATES = institution_contract_templates()
_INSTITUTION_CONTRACTS_BY_ID = {
    item["id"]: item for item in _INSTITUTION_CONTRACT_TEMPLATES
}


def list_institution_contract_templates() -> list[Json]:
    return deepcopy(_INSTITUTION_CONTRACT_TEMPLATES)


def get_institution_contract_template(template_id: str) -> Json | None:
    item = _INSTITUTION_CONTRACTS_BY_ID.get(template_id)
    return deepcopy(item) if item else None


def institution_contract_catalog_metadata() -> Json:
    contract_type_count = sum(len(item["contracts"]) for item in INSTITUTIONS)
    return {
        "name": "Institution Contracts",
        "jurisdiction": "Kingdom of Lesotho",
        "lawProfileVersion": LAW_PROFILE_VERSION,
        "institutionCount": len(INSTITUTIONS),
        "documentTypeCount": contract_type_count,
        "styleCount": len(STYLE_PRESETS),
        "templateCount": len(_INSTITUTION_CONTRACT_TEMPLATES),
        "styles": [deepcopy(item) for item in STYLE_PRESETS],
        "packs": [
            {
                "slug": institution["slug"],
                "name": institution["name"],
                "category": institution["category"],
                "documentTypeCount": len(institution["contracts"]),
                "templateCount": len(institution["contracts"]) * len(STYLE_PRESETS),
                "riskLevel": "high",
                "laws": [_law_source(key) for key in institution["laws"]],
            }
            for institution in INSTITUTIONS
        ],
    }
