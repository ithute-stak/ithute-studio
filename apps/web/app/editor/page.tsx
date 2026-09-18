"use client";

import { useEffect, useMemo, useState } from "react";
import { StudioEditor } from "@ithute/document-editor";
import {
  DEFAULT_DOCUMENT_SETTINGS,
  emptyDoc,
  type DataDictionary,
  type IthuteDocumentV1,
} from "@ithute/document-schema";

const dictionary: DataDictionary = {
  id: "studio-financial-dictionary",
  name: "Studio business & accounting data",
  version: "1",
  fields: [
    { path: "company.name", label: "Company name", type: "text", group: "Company" },
    { path: "company.registrationNumber", label: "Registration number", type: "text", group: "Company" },
    { path: "company.address", label: "Company address", type: "text", group: "Company" },
    { path: "company.phone", label: "Company phone", type: "text", group: "Company" },
    { path: "company.email", label: "Company email", type: "text", group: "Company" },
    { path: "counterparty.name", label: "Customer / supplier", type: "text", group: "Account" },
    { path: "recipient.name", label: "Recipient name", type: "text", group: "Account" },
    { path: "recipient.address", label: "Recipient address", type: "text", group: "Account" },
    { path: "document.number", label: "Document number", type: "text", group: "Document" },
    { path: "document.reference", label: "Reference", type: "text", group: "Document" },
    { path: "document.date", label: "Document date", type: "date", group: "Document" },
    { path: "document.currency", label: "Currency", type: "text", group: "Document" },
    { path: "document.notes", label: "Notes", type: "text", group: "Document" },
    { path: "totals.subtotal", label: "Subtotal", type: "currency", group: "Totals" },
    { path: "totals.tax", label: "Tax", type: "currency", group: "Totals" },
    { path: "totals.total", label: "Total", type: "currency", group: "Totals" },
    { path: "totals.balanceDue", label: "Balance due", type: "currency", group: "Totals" },
    { path: "verification.code", label: "Verification code", type: "text", group: "Verification" },
    { path: "verification.url", label: "Verification URL", type: "url", group: "Verification" },
    { path: "approval.preparedBy", label: "Prepared by", type: "text", group: "Approval" },
    { path: "approval.approvedBy", label: "Approved by", type: "text", group: "Approval" },
    {
      path: "items",
      label: "Line items",
      type: "collection",
      group: "Collections",
      itemFields: [
        { path: "description", label: "Description", type: "text" },
        { path: "quantity", label: "Quantity", type: "number" },
        { path: "unitPrice", label: "Unit price", type: "currency" },
        { path: "tax", label: "Tax", type: "currency" },
        { path: "total", label: "Total", type: "currency" },
      ],
    },
    {
      path: "transactions",
      label: "Transactions",
      type: "collection",
      group: "Collections",
      itemFields: [
        { path: "date", label: "Date", type: "date" },
        { path: "reference", label: "Reference", type: "text" },
        { path: "description", label: "Description", type: "text" },
        { path: "debit", label: "Debit", type: "currency" },
        { path: "credit", label: "Credit", type: "currency" },
        { path: "balance", label: "Balance", type: "currency" },
      ],
    },
  ],
};

function createDocument(): IthuteDocumentV1 {
  const now = new Date().toISOString();
  return {
    schemaVersion: 1,
    id: "demo-document",
    workspaceId: "demo",
    properties: { title: "Untitled document", author: "Ithute Document Studio", language: "en" },
    settings: DEFAULT_DOCUMENT_SETTINGS,
    header: emptyDoc(),
    body: {
      type: "doc",
      content: [
        { type: "heading", attrs: { level: 1 }, content: [{ type: "text", text: "Document title" }] },
        { type: "paragraph", content: [{ type: "text", text: "Start writing here, or use the Data panel to insert variables." }] },
      ],
    },
    footer: emptyDoc(),
    variables: {},
    version: 1,
    createdAt: now,
    updatedAt: now,
  };
}

export default function EditorPage() {
  const initial = useMemo(createDocument, []);
  const [saved, setSaved] = useState(initial);

  useEffect(() => {
    const templateId = new URLSearchParams(window.location.search).get("templateId");
    if (!templateId) return;
    const base = process.env.NEXT_PUBLIC_DOCUMENT_STUDIO_API || "http://localhost:8000";
    fetch(`${base}/v1/templates/${encodeURIComponent(templateId)}`)
      .then(async (response) => {
        if (!response.ok) throw new Error(await response.text());
        return response.json() as Promise<{ document?: IthuteDocumentV1 }>;
      })
      .then((template) => {
        if (template.document) {
          const now = new Date().toISOString();
          setSaved({ ...template.document, id: crypto.randomUUID(), createdAt: now, updatedAt: now, version: 1 });
        }
      })
      .catch(() => undefined);
  }, []);

  const exportDocument = async (document: IthuteDocumentV1, format: "pdf" | "docx") => {
    const base = process.env.NEXT_PUBLIC_DOCUMENT_STUDIO_API || "http://localhost:8000";
    const response = await fetch(`${base}/v1/render`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ document, format }),
    });
    if (!response.ok) throw new Error(await response.text());
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = window.document.createElement("a");
    anchor.href = url;
    anchor.download = `${document.properties.title || "document"}.${format}`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <StudioEditor
      document={saved}
      dataDictionary={dictionary}
      onSave={async (next) => {
        localStorage.setItem("ithute-document-studio-demo", JSON.stringify(next));
        setSaved(next);
        return next;
      }}
      onExport={exportDocument}
    />
  );
}
