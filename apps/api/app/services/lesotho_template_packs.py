from __future__ import annotations

import re
import uuid
from copy import deepcopy
from typing import Any

from app.services.accounting_templates import STYLE_PRESETS

Json = dict[str, Any]
CATALOG_TIMESTAMP = "2026-09-18T00:00:00+00:00"
LAW_PROFILE_VERSION = "LS-2026-09-18"

LAW_SOURCES: dict[str, Json] = {
    "labour-2024": {
        "title": "Labour Act, 2024",
        "citation": "Act 3 of 2024",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2024/3/eng@2024-04-02",
    },
    "data-protection-2012": {
        "title": "Data Protection Act, 2012",
        "citation": "Act 5 of 2012",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2012/5/eng@2012-02-22",
    },
    "companies-2011": {
        "title": "Companies Act, 2011",
        "citation": "Act 18 of 2011",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2011/18/eng@2011-09-02",
    },
    "financial-institutions-2012": {
        "title": "Financial Institutions Act, 2012",
        "citation": "Act 3 of 2012",
        "authority": "Kingdom of Lesotho / Central Bank of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2012/3/eng@2012-02-27",
    },
    "financial-consumer-2022": {
        "title": "Financial Consumer Protection Act, 2022",
        "citation": "Act 7 of 2022",
        "authority": "Central Bank of Lesotho",
        "sourceUrl": "https://centralbank.org.ls/supervision-acts/",
    },
    "financial-disclosure-2023": {
        "title": "Financial Consumer Protection (Disclosure of Credit Information) Regulations, 2023",
        "citation": "Legal Notice 24 of 2023",
        "authority": "Central Bank of Lesotho",
        "sourceUrl": "https://centralbank.org.ls/legislations/",
    },
    "financial-marketing-2024": {
        "title": "Financial Consumer Protection (Advertisement and Marketing) Regulations, 2024",
        "citation": "2024 Regulations",
        "authority": "Central Bank of Lesotho",
        "sourceUrl": "https://centralbank.org.ls/legislations/",
    },
    "credit-reporting-2011": {
        "title": "Credit Reporting Act, 2011",
        "citation": "Act 1 of 2012",
        "authority": "Kingdom of Lesotho / Central Bank of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2012/1/eng@2012-01-24",
    },
    "aml-2008": {
        "title": "Money Laundering and Proceeds of Crime Act, 2008",
        "citation": "Act 4 of 2008",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2008/4/eng@2015-09-25",
    },
    "aml-regs-2019": {
        "title": "Money Laundering and Proceeds of Crime Regulations, 2019",
        "citation": "Legal Notice 29 of 2019",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/ln/2019/29/eng@2019-03-29",
    },
    "money-lenders": {
        "title": "Money Lenders Order, 1989 and Money Lenders Amendment Act, 1993",
        "citation": "Micro-finance legislation",
        "authority": "Central Bank of Lesotho",
        "sourceUrl": "https://centralbank.org.ls/legislations/",
    },
    "procurement-2023": {
        "title": "Public Procurement Act, 2023",
        "citation": "Act 3 of 2023",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://finance.gov.ls/PDFDocuments/Act%20No.%203%20of%202023-638267642877509583.pdf",
    },
    "pfma-2011": {
        "title": "Public Financial Management and Accountability Act, 2011",
        "citation": "Act 12 of 2011",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2011/12/eng@2011-06-17",
    },
    "road-traffic-1981": {
        "title": "Road Traffic Act, 1981",
        "citation": "Act 8 of 1981",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/1981/8/eng@1981-12-31",
    },
    "road-regs-1981": {
        "title": "Road Traffic Regulations, 1981",
        "citation": "Legal Notice 84 of 1981",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/ln/1981/84/eng@1981-12-31",
    },
    "building-control-1995": {
        "title": "Building Control Act, 1995",
        "citation": "Act 8 of 1995",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/1995/8/eng@1995-12-31",
    },
    "environment-2008": {
        "title": "Environment Act, 2008",
        "citation": "Act 10 of 2008",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2008/10/eng@2008-12-05",
    },
    "education-2010": {
        "title": "Education Act, 2010",
        "citation": "Act 3 of 2010",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2010/3/eng@2010-03-15",
    },
    "payments-2014": {
        "title": "Payment Systems Act, 2014",
        "citation": "Payment Systems Act, 2014",
        "authority": "Central Bank of Lesotho",
        "sourceUrl": "https://centralbank.org.ls/payment-systems2/",
    },
    "payments-regs-2017": {
        "title": "Payment Systems Regulations, 2017",
        "citation": "2017 Regulations",
        "authority": "Central Bank of Lesotho",
        "sourceUrl": "https://centralbank.org.ls/payment-systems2/",
    },
    "land-2010": {
        "title": "Land Act, 2010",
        "citation": "Act 8 of 2010",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2010/8/eng@2010-06-14",
    },
    "land-regs-2011": {
        "title": "Land Regulations, 2011",
        "citation": "Legal Notice 21 of 2011",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/ln/2011/21/eng@2011-02-24",
    },
    "insurance-2014": {
        "title": "Insurance Act, 2014",
        "citation": "Act 12 of 2014",
        "authority": "Kingdom of Lesotho / Central Bank of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2014/12/eng@2014-09-26",
    },
    "insurance-codes-2016": {
        "title": "Insurance Good Practice Codes, 2016",
        "citation": "Insurer and intermediary good-practice codes",
        "authority": "Central Bank of Lesotho",
        "sourceUrl": "https://centralbank.org.ls/legislations/",
    },
    "public-health-1970": {
        "title": "Public Health Order, 1970",
        "citation": "Public Health Order, 1970",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/",
    },
    "vat-2001": {
        "title": "Value Added Tax Act, 2001",
        "citation": "Act 9 of 2001",
        "authority": "Kingdom of Lesotho",
        "sourceUrl": "https://lesotholii.org/akn/ls/act/2001/9/eng@2001-12-31",
    },
}

PACKS: tuple[Json, ...] = (
    {
        "slug": "hr-employment",
        "name": "HR & Employment",
        "category": "hr",
        "laws": ["labour-2024", "data-protection-2012"],
        "risk": "high",
        "checks": [
            "Apply Labour Act 2024 minimum standards; contractual terms may improve but must not undercut statutory rights.",
            "For probation, do not exceed four months unless written leave is obtained from the Labour Commissioner.",
            "For indefinite employment termination, validate statutory notice by length of service and use written notice.",
            "Protect employee personal information in accordance with the Data Protection Act 2012.",
        ],
        "documents": [
            "Employment Contract", "Offer Letter", "Appointment Letter", "Confirmation of Employment",
            "Probation Letter", "Promotion Letter", "Salary Adjustment Letter", "Warning Letter",
            "Disciplinary Notice", "Suspension Letter", "Termination Letter", "Resignation Acceptance",
            "Leave Application Form", "Leave Approval Letter", "Payslip Cover Letter",
            "Staff Performance Evaluation", "Job Description", "Interview Scorecard", "Onboarding Checklist",
            "Employee Clearance Form", "Certificate of Service", "Employment Reference Letter", "Staff ID Form",
        ],
    },
    {
        "slug": "legal-corporate",
        "name": "Legal & Corporate",
        "category": "legal",
        "laws": ["companies-2011", "data-protection-2012"],
        "risk": "high",
        "checks": [
            "Confirm legal names, registration numbers, authority and capacity of all signatories.",
            "Company resolutions and governance documents must match the Companies Act 2011 and the company's constitution.",
            "Personal information clauses must comply with the Data Protection Act 2012.",
            "Execution-sensitive documents require review for witnessing, notarisation, registration or filing requirements applicable to the transaction.",
        ],
        "documents": [
            "Non-Disclosure Agreement", "Service Agreement", "Supplier Agreement", "Partnership Agreement",
            "Shareholder Resolution", "Board Resolution", "Meeting Minutes", "Memorandum of Understanding",
            "Loan Agreement", "Acknowledgement of Debt", "Settlement Agreement", "Payment Plan Agreement",
            "Demand Letter", "Breach Notice", "Notice of Termination", "Affidavit", "Declaration", "Consent Form",
            "Power of Attorney", "Company Resolution", "Legal Notice",
        ],
    },
    {
        "slug": "lending-credit",
        "name": "Lending & Credit",
        "category": "lending",
        "laws": [
            "financial-consumer-2022", "financial-disclosure-2023", "financial-institutions-2012",
            "credit-reporting-2011", "data-protection-2012", "aml-2008", "aml-regs-2019", "money-lenders",
        ],
        "risk": "high",
        "checks": [
            "Provide clear, fair and legible pre-contract information and a Key Facts Statement where required.",
            "Disclose interest, fees, charges, total cost, repayment schedule, late-payment consequences and complaint channels.",
            "Before enforcement, give written default notice stating the overdue amount, consumer rights and how the default can be remedied.",
            "Process credit information and personal data only for lawful purposes and with required notices/consents.",
            "Complete applicable KYC/AML checks and confirm the lender holds any licence or registration required for its activity.",
        ],
        "documents": [
            "Loan Application Form", "Loan Offer Letter", "Loan Agreement", "Repayment Schedule",
            "Settlement Quotation", "Settlement Certificate", "Account Statement", "Arrears Notice",
            "Payment Reminder", "Demand Letter", "Restructuring Agreement", "Affordability Report",
            "Credit Analysis Report", "Approval Letter", "Rejection Letter", "Disbursement Confirmation",
            "Deduction Authority Form", "Clearance Letter",
        ],
    },
    {
        "slug": "general-business",
        "name": "General Business",
        "category": "business",
        "laws": ["companies-2011", "data-protection-2012", "vat-2001"],
        "risk": "medium",
        "checks": [
            "Use the registered business name and company particulars where applicable.",
            "Protect client and contact information under the Data Protection Act 2012.",
            "Where a document is a tax invoice or records taxable consideration, validate applicable VAT requirements separately.",
        ],
        "documents": [
            "Company Profile", "Quotation", "Business Proposal", "Tender Response", "Purchase Request",
            "Business Letter", "Internal Memo", "Meeting Minutes", "Project Proposal", "Project Status Report",
            "Service Report", "Client Onboarding Form", "Customer Complaint Form", "Service Level Agreement",
            "Completion Certificate", "Handover Certificate", "Company Registration Pack",
        ],
    },
    {
        "slug": "procurement-supply-chain",
        "name": "Procurement & Supply Chain",
        "category": "procurement",
        "laws": ["procurement-2023", "pfma-2011", "data-protection-2012"],
        "risk": "high",
        "checks": [
            "For public procurement, use the Public Procurement Act 2023 and applicable regulations, solicitation documents and thresholds in force for the procuring entity.",
            "Preserve transparency, competition, value-for-money, ethics, approvals and audit trail.",
            "Do not use public-procurement forms as private-sector authority to bypass required approvals or prescribed forms.",
        ],
        "documents": [
            "Request for Quotation", "Request for Tender", "Supplier Registration Form", "Bid Evaluation Sheet",
            "Purchase Requisition", "Purchase Order", "Delivery Note", "Goods Received Note",
            "Supplier Performance Report", "Stock Transfer Form", "Stock Adjustment Form", "Inventory Count Sheet",
            "Procurement Approval Document",
        ],
    },
    {
        "slug": "fleet-transport",
        "name": "Fleet & Transport",
        "category": "fleet",
        "laws": ["road-traffic-1981", "road-regs-1981", "labour-2024", "data-protection-2012"],
        "risk": "medium",
        "checks": [
            "Record vehicle registration, licensing, roadworthiness and driver-licence details relevant to the operation.",
            "Accident and inspection records must not substitute for statutory reporting to traffic, police or insurance authorities where required.",
            "Protect driver and passenger personal information.",
        ],
        "documents": [
            "Vehicle Inspection Form", "Trip Sheet", "Fuel Log", "Maintenance Request", "Service Record",
            "Accident Report", "Driver Assignment Form", "Vehicle Handover Form", "Mileage Report", "Tyre Register",
            "Licence and Permit Tracker", "Route Sheet", "Load Manifest", "Vehicle Cost Report", "Fleet Availability Report",
        ],
    },
    {
        "slug": "construction-engineering",
        "name": "Construction & Engineering",
        "category": "construction",
        "laws": ["building-control-1995", "environment-2008", "labour-2024", "data-protection-2012"],
        "risk": "high",
        "checks": [
            "Confirm permits, approvals, occupancy requirements and competent professional sign-off required by the Building Control Act 1995.",
            "Flag activities requiring environmental assessment, mitigation or environmental approvals under the Environment Act 2008.",
            "Workplace and employment records must meet Labour Act 2024 standards.",
        ],
        "documents": [
            "Construction Quotation", "Bill of Quantities", "Site Instruction", "Daily Site Report",
            "Material Requisition", "Material Usage Report", "Progress Certificate", "Variation Order", "Snag List",
            "Completion Certificate", "Subcontractor Agreement", "Equipment Inspection Report",
            "Health and Safety Form", "Incident Report", "Project Handover Form", "Project Cost Report",
        ],
    },
    {
        "slug": "education",
        "name": "Education",
        "category": "education",
        "laws": ["education-2010", "data-protection-2012", "labour-2024"],
        "risk": "medium",
        "checks": [
            "School governance and teaching-service documents must follow the Education Act 2010 and applicable Ministry/Teaching Service rules.",
            "Student records, reports and identifiers are personal information and must be handled under the Data Protection Act 2012.",
            "Employment documents for school staff remain subject to the Labour Act 2024 where applicable.",
        ],
        "documents": [
            "Admission Letter", "Enrolment Form", "Report Card", "Academic Transcript", "Certificate",
            "Attendance Report", "Teacher Evaluation", "Fee Statement", "Fee Receipt", "Disciplinary Notice",
            "Parent Letter", "Exam Timetable", "Lesson Plan", "School Report", "Student Clearance Form",
            "Graduation Certificate",
        ],
    },
    {
        "slug": "risk-compliance",
        "name": "Risk & Compliance",
        "category": "risk",
        "laws": ["data-protection-2012", "aml-2008", "aml-regs-2019", "companies-2011"],
        "risk": "high",
        "checks": [
            "Use risk-based KYC/AML controls where the organisation is an accountable institution or otherwise subject to AML/CFT duties.",
            "Record beneficial-owner and source information only where lawfully required and protect it appropriately.",
            "Do not mark a compliance certificate as statutory approval unless issued by an authority empowered by law.",
        ],
        "documents": [
            "Risk Assessment", "Risk Register", "Incident Report", "Compliance Report", "Audit Finding",
            "Corrective Action Plan", "Due Diligence Report", "KYC Form", "AML Review Form",
            "Policy Acknowledgement Form", "Control Testing Report", "Business Continuity Report", "Compliance Certificate",
        ],
    },
    {
        "slug": "payments-banking",
        "name": "Payments & Banking",
        "category": "payments",
        "laws": [
            "payments-2014", "payments-regs-2017", "financial-consumer-2022", "data-protection-2012",
            "aml-2008", "aml-regs-2019",
        ],
        "risk": "high",
        "checks": [
            "Use only for payment services and instruments the issuer/provider is authorised to provide.",
            "Keep transaction references, payer/payee information, fees and settlement status clear and auditable.",
            "Apply consumer-protection, data-protection and AML/CFT duties to regulated payment activity.",
        ],
        "documents": [
            "Payment Confirmation", "Remittance Advice", "Transaction Receipt", "Settlement Report", "Payout Report",
            "Merchant Statement", "Reconciliation Report", "Bank Instruction Letter", "Direct Debit Mandate",
            "Payment Authorisation Form", "Failed Payment Notice",
        ],
    },
    {
        "slug": "government-official",
        "name": "Government & Official",
        "category": "government",
        "laws": ["procurement-2023", "pfma-2011", "data-protection-2012"],
        "risk": "high",
        "checks": [
            "Use the issuing body's statutory authority, prescribed form and delegation rules where legislation requires them.",
            "Government procurement and financial records must preserve approvals, value-for-money controls and audit trail.",
            "A Studio template must never imply a permit, licence or certificate was issued by government unless an authorised officer actually issues it.",
        ],
        "documents": [
            "Official Letter", "Official Certificate", "Permit", "Application Form", "Acknowledgement Letter",
            "Public Notice", "Internal Memorandum", "Departmental Report", "Government Procurement Document",
            "Inspection Report", "Approval Letter", "Official Receipt",
        ],
    },
    {
        "slug": "property-real-estate",
        "name": "Property & Real Estate",
        "category": "property",
        "laws": ["land-2010", "land-regs-2011", "data-protection-2012", "building-control-1995"],
        "risk": "high",
        "checks": [
            "Record the correct plot/lease/title identifiers and verify the right of the party dealing with the land.",
            "Identify transactions requiring Commissioner consent, registration, prescribed forms, survey or Deeds Registry action.",
            "Do not treat a private sale/transfer template as proof that title has legally transferred before required consent/registration is complete.",
        ],
        "documents": [
            "Lease Agreement", "Rental Invoice", "Rent Receipt", "Tenant Statement", "Property Inspection Report",
            "Property Handover Form", "Eviction Notice", "Maintenance Request", "Property Valuation Report",
            "Sale Agreement", "Ownership Transfer Document",
        ],
    },
    {
        "slug": "insurance",
        "name": "Insurance",
        "category": "insurance",
        "laws": ["insurance-2014", "insurance-codes-2016", "financial-consumer-2022", "data-protection-2012"],
        "risk": "high",
        "checks": [
            "Only licensed/authorised insurers and intermediaries should issue regulated insurance documents within their authority.",
            "Disclose material terms, exclusions, premiums, excesses, complaints routes and consumer rights clearly.",
            "Protect claimant, insured and beneficiary personal information.",
        ],
        "documents": [
            "Insurance Quotation", "Policy Schedule", "Claim Form", "Claim Acknowledgement Letter",
            "Claim Assessment Report", "Loss Report", "Settlement Letter", "Proof of Cover Letter",
            "Renewal Notice", "Cancellation Notice",
        ],
    },
    {
        "slug": "medical-clinic",
        "name": "Medical / Clinic Administration",
        "category": "health",
        "laws": ["data-protection-2012", "public-health-1970"],
        "risk": "high",
        "checks": [
            "Health information is sensitive personal information; restrict access and collect only information necessary for the stated purpose.",
            "Clinical certificates, referrals and discharge records must be completed/authorised by appropriately qualified personnel where required.",
            "Patient consent forms must identify the specific procedure/information use and must not be used to waive rights that cannot lawfully be waived.",
        ],
        "documents": [
            "Appointment Letter", "Clinic Invoice", "Clinic Receipt", "Referral Letter", "Medical Certificate",
            "Patient Consent Form", "Patient Registration Form", "Discharge Summary",
        ],
    },
    {
        "slug": "marketing-sales",
        "name": "Marketing & Sales",
        "category": "marketing",
        "laws": ["data-protection-2012", "companies-2011", "financial-marketing-2024"],
        "risk": "medium",
        "checks": [
            "Marketing use of personal information must comply with the Data Protection Act 2012.",
            "For financial products/services, apply the Financial Consumer Protection marketing and advertisement rules and avoid misleading/deceptive claims.",
            "Do not present forecasts, performance claims or endorsements as guarantees unless legally supportable and evidenced.",
        ],
        "documents": [
            "Sales Proposal", "Media Plan", "Campaign Report", "Client Brief", "Marketing Quotation",
            "Performance Report", "Content Calendar", "Sponsorship Proposal", "Partnership Proposal",
            "Campaign Completion Report",
        ],
    },
    {
        "slug": "certificates-credentials",
        "name": "Certificates & Credentials",
        "category": "certificates",
        "laws": ["data-protection-2012", "education-2010", "companies-2011"],
        "risk": "medium",
        "checks": [
            "Only an organisation with authority to certify the stated fact should issue the credential.",
            "Verification QR/code must resolve to an authentic Studio record and must not expose unnecessary personal information.",
            "Education credentials must not imply Ministry or statutory accreditation unless that status is valid.",
        ],
        "documents": [
            "Training Certificate", "Achievement Certificate", "Attendance Certificate", "Employment Certificate",
            "Completion Certificate", "Appreciation Certificate", "Membership Certificate", "Compliance Certificate",
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


def _p(*nodes: Json, align: str = "left", border: bool = False) -> Json:
    return {
        "type": "paragraph",
        "attrs": {"textAlign": align, **({"border": True} if border else {})},
        "content": list(nodes),
    }


def _h(value: str, level: int = 1) -> Json:
    return {"type": "heading", "attrs": {"level": level}, "content": [_text(value)]}


def _signature_table() -> Json:
    return {
        "type": "table",
        "content": [
            {
                "type": "tableRow",
                "content": [
                    {"type": "tableCell", "content": [_p(_text("Name / Authorised signatory", bold=True)), _p(_var("signatory.name"))]},
                    {"type": "tableCell", "content": [_p(_text("Signature / Date", bold=True)), _p(_var("signatory.date"))]},
                ],
            }
        ],
    }


def _family(label: str) -> str:
    lowered = label.casefold()
    if "agreement" in lowered or "contract" in lowered or "memorandum of understanding" in lowered:
        return "agreement"
    if "certificate" in lowered:
        return "certificate"
    if any(word in lowered for word in ("letter", "notice", "memo", "memorandum")):
        return "letter"
    if any(word in lowered for word in ("form", "application", "checklist", "scorecard", "mandate", "authority")):
        return "form"
    if any(word in lowered for word in ("report", "assessment", "analysis", "statement", "schedule", "register", "tracker", "log", "sheet", "timetable", "calendar", "plan", "minutes")):
        return "report"
    return "document"


def _body(pack: Json, label: str) -> Json:
    family = _family(label)
    content: list[Json] = [
        _h(label),
        _p(_text("Kingdom of Lesotho • Law-aware Studio template", bold=True)),
        _p(_text("Document No.: ", bold=True), _var("document.number")),
        _p(_text("Date: ", bold=True), _var("document.date")),
    ]
    if family == "agreement":
        content.extend([
            _h("Parties", 2),
            _p(_text("Party A: ", bold=True), _var("partyA.name")),
            _p(_text("Party B: ", bold=True), _var("partyB.name")),
            _h("Background and purpose", 2),
            _p(_var("document.purpose"), border=True),
            _h("Terms", 2),
            _p(_var("document.terms"), border=True),
            _h("Governing law", 2),
            _p(_text("This document is governed by the laws of the Kingdom of Lesotho, subject to any mandatory law and sector-specific requirement that applies to the transaction.")),
        ])
    elif family == "letter":
        content.extend([
            _p(_text("To: ", bold=True), _var("recipient.name")),
            _p(_var("recipient.address")),
            _p(_text("Reference: ", bold=True), _var("document.reference")),
            _h("Subject", 2),
            _p(_var("document.subject"), border=True),
            _p(_var("document.body"), border=True),
        ])
    elif family == "certificate":
        content.extend([
            _h("Certification", 2),
            _p(_text("This certifies that ", bold=True), _var("subject.name"), _text(" — "), _var("document.body"), align="center", border=True),
            _p(_text("Verification code: ", bold=True), _var("verification.code"), align="center"),
            {"type": "qrCode", "attrs": {"value": "{{verification.url}}", "label": "Verify this Studio credential"}},
        ])
    elif family == "form":
        content.extend([
            _h("Applicant / Subject details", 2),
            _p(_text("Name: ", bold=True), _var("subject.name")),
            _p(_text("ID / Registration No.: ", bold=True), _var("subject.identifier")),
            _p(_text("Contact: ", bold=True), _var("subject.contact")),
            _h("Information", 2),
            _p(_var("document.body"), border=True),
            _p(_text("Declaration / consent: ", bold=True), _var("document.declaration"), border=True),
        ])
    else:
        content.extend([
            _h("Details", 2),
            _p(_text("Subject / Account: ", bold=True), _var("subject.name")),
            _p(_text("Reference: ", bold=True), _var("document.reference")),
            _p(_var("document.body"), border=True),
            _h("Findings / Notes", 2),
            _p(_var("document.notes"), border=True),
        ])

    if pack["slug"] == "hr-employment" and label == "Employment Contract":
        content.extend([
            _h("Employment particulars", 2),
            _p(_text("Employment type: ", bold=True), _var("employment.type")),
            _p(_text("Start date: ", bold=True), _var("employment.startDate")),
            _p(_text("Job title / duties: ", bold=True), _var("employment.jobTitle")),
            _p(_text("Normal place of work: ", bold=True), _var("employment.workplace")),
            _p(_text("Remuneration: ", bold=True), _var("employment.remuneration")),
            _p(_text("Ordinary hours: ", bold=True), _var("employment.hours")),
            _p(_text("Probation, if any: ", bold=True), _var("employment.probation")),
            _p(_text("Leave and benefits: ", bold=True), _var("employment.leave")),
            _p(_text("Termination / notice: ", bold=True), _var("employment.termination")),
        ])
    if pack["slug"] == "lending-credit" and label in {"Loan Offer Letter", "Loan Agreement"}:
        content.extend([
            _h("Key financial terms", 2),
            _p(_text("Principal: ", bold=True), _var("credit.principal")),
            _p(_text("Interest / pricing: ", bold=True), _var("credit.interest")),
            _p(_text("Fees and charges: ", bold=True), _var("credit.fees")),
            _p(_text("Total cost of credit: ", bold=True), _var("credit.totalCost")),
            _p(_text("Repayment schedule: ", bold=True), _var("credit.repayment")),
            _p(_text("Late/default consequences: ", bold=True), _var("credit.defaultTerms")),
            _p(_text("Complaints contact: ", bold=True), _var("credit.complaints")),
            _p(_text("Key Facts Statement acknowledgement: ", bold=True), _var("credit.kfsAcknowledgement")),
        ])
    if pack["slug"] == "lending-credit" and label in {"Arrears Notice", "Demand Letter"}:
        content.extend([
            _h("Pre-enforcement information", 2),
            _p(_text("Amount overdue: ", bold=True), _var("credit.amountOverdue")),
            _p(_text("How the default may be remedied: ", bold=True), _var("credit.remedy"), border=True),
            _p(_text("Consumer rights / complaint route: ", bold=True), _var("credit.consumerRights"), border=True),
        ])
    if pack["slug"] == "property-real-estate" and label in {"Lease Agreement", "Sale Agreement", "Ownership Transfer Document"}:
        content.extend([
            _h("Land particulars", 2),
            _p(_text("Plot / lease / title no.: ", bold=True), _var("property.titleNumber")),
            _p(_text("Location: ", bold=True), _var("property.location")),
            _p(_text("Commissioner consent / registration status: ", bold=True), _var("property.registrationStatus")),
        ])

    content.extend([
        _h("Lesotho compliance check", 2),
        *[_p(_text(f"• {check}")) for check in pack["checks"]],
        _p(_text("Studio compliance profile: ", bold=True), _text(LAW_PROFILE_VERSION)),
        _signature_table(),
    ])
    return {"type": "doc", "content": content}


def _header(pack_name: str, label: str) -> Json:
    return {
        "type": "doc",
        "content": [
            _p(_var("company.name")),
            _p(_text(pack_name.upper(), bold=True)),
            _p(_text(label, bold=True)),
        ],
    }


def _footer(pack: Json) -> Json:
    return {
        "type": "doc",
        "content": [
            _p(_text("Kingdom of Lesotho • "), _text(str(pack["name"])), _text(" • Law profile "), _text(LAW_PROFILE_VERSION)),
            _p(_var("company.address"), _text(" • "), _var("company.phone"), _text(" • "), _var("company.email")),
            _p(_text("Document "), _var("document.number"), _text(" • Verify "), _var("verification.code")),
        ],
    }


def _template(pack: Json, label: str, style: Json) -> Json:
    slug = _slug(label)
    template_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://ithute.studio/templates/lesotho/{pack['slug']}/{slug}/{style['slug']}"))
    document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{template_id}/document"))
    laws = [deepcopy(LAW_SOURCES[key]) for key in pack["laws"]]
    compliance = {
        "jurisdiction": "Kingdom of Lesotho",
        "profileVersion": LAW_PROFILE_VERSION,
        "verifiedAt": "2026-09-18",
        "riskLevel": pack["risk"],
        "legalReviewRequired": pack["risk"] == "high",
        "laws": laws,
        "requiredChecks": deepcopy(pack["checks"]),
        "note": "Template-level compliance profile. Facts, licences, prescribed forms and execution requirements must still be validated before issue.",
    }
    document = {
        "schemaVersion": 1,
        "id": document_id,
        "workspaceId": "system",
        "templateId": template_id,
        "properties": {
            "title": label,
            "subject": f"{pack['name']} — {label}",
            "author": "Ithute Document Studio",
            "category": pack["name"],
            "keywords": ["Lesotho", pack["slug"], slug, style["slug"]],
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
            "documentLabel": label,
            "jurisdictionBadge": "LESOTHO",
        },
        "compliance": compliance,
        "header": _header(str(pack["name"]), label),
        "body": _body(pack, label),
        "footer": _footer(pack),
        "variables": {},
        "createdAt": CATALOG_TIMESTAMP,
        "updatedAt": CATALOG_TIMESTAMP,
        "version": 1,
    }
    return {
        "id": template_id,
        "workspaceId": None,
        "name": f"{label} — {style['name']}",
        "description": f"Lesotho law-aware {label.lower()} template with {style['name']} styling.",
        "category": pack["category"],
        "collection": pack["name"],
        "pack": pack["slug"],
        "documentType": slug,
        "documentTypeLabel": label,
        "family": _family(label),
        "stylePreset": style["slug"],
        "styleName": style["name"],
        "style": deepcopy(style),
        "jurisdiction": "LS",
        "compliance": compliance,
        "tags": ["Lesotho", pack["slug"], slug, style["slug"]],
        "isPublished": True,
        "isBuiltIn": True,
        "document": document,
        "createdAt": CATALOG_TIMESTAMP,
        "updatedAt": CATALOG_TIMESTAMP,
    }


def lesotho_templates() -> list[Json]:
    return [
        _template(pack, label, style)
        for pack in PACKS
        for label in pack["documents"]
        for style in STYLE_PRESETS
    ]


_LESOTHO_TEMPLATES = lesotho_templates()
_LESOTHO_BY_ID = {item["id"]: item for item in _LESOTHO_TEMPLATES}


def list_lesotho_templates() -> list[Json]:
    return deepcopy(_LESOTHO_TEMPLATES)


def get_lesotho_template(template_id: str) -> Json | None:
    item = _LESOTHO_BY_ID.get(template_id)
    return deepcopy(item) if item else None


def lesotho_catalog_metadata() -> Json:
    document_count = sum(len(pack["documents"]) for pack in PACKS)
    return {
        "name": "Lesotho Business & Institutional Templates",
        "jurisdiction": "Kingdom of Lesotho",
        "lawProfileVersion": LAW_PROFILE_VERSION,
        "packCount": len(PACKS),
        "documentTypeCount": document_count,
        "styleCount": len(STYLE_PRESETS),
        "templateCount": document_count * len(STYLE_PRESETS),
        "packs": [
            {
                "slug": pack["slug"],
                "name": pack["name"],
                "category": pack["category"],
                "documentTypeCount": len(pack["documents"]),
                "templateCount": len(pack["documents"]) * len(STYLE_PRESETS),
                "riskLevel": pack["risk"],
                "laws": [deepcopy(LAW_SOURCES[key]) for key in pack["laws"]],
            }
            for pack in PACKS
        ],
        "styles": [deepcopy(style) for style in STYLE_PRESETS],
    }
