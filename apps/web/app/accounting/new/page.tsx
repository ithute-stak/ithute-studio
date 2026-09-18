"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type Json = Record<string, any>;
type TemplateItem = {
  id: string;
  name: string;
  collection?: string;
  documentTypeLabel?: string;
  styleName?: string;
  family?: string;
};
type FormSchema = {
  templateId: string;
  documentType?: string;
  documentTypeLabel?: string;
  family: string;
  styleName?: string;
  documentPrefix?: string;
  collectionPath?: string | null;
  collectionColumns: Array<{ label: string; path: string; format: string }>;
  showCounterparty: boolean;
  showLetterFields: boolean;
  showPayrollFields: boolean;
};

type PreviewPayload = {
  data: Json;
  document: Json;
};

const apiBase = () => process.env.NEXT_PUBLIC_DOCUMENT_STUDIO_API || "http://localhost:8000";
const today = () => new Date().toISOString().slice(0, 10);

function initialData(): Json {
  return {
    company: { name: "", registrationNumber: "", address: "", phone: "", email: "" },
    counterparty: { name: "" },
    recipient: { name: "", address: "" },
    document: { number: "", reference: "", date: today(), currency: "LSL", notes: "" },
    totals: { amountPaid: 0 },
    approval: { preparedBy: "", approvedBy: "" },
    verification: { code: "", url: "" },
    letter: { salutation: "Dear Sir/Madam,", body: "", closing: "Yours faithfully," },
    employee: { name: "", number: "" },
    payroll: { period: "" },
    earnings: [{ description: "Basic pay", amount: 0 }],
    deductions: [{ description: "", amount: 0 }],
  };
}

function setPath(source: Json, path: string, value: unknown): Json {
  const copy = structuredClone(source);
  const parts = path.split(".");
  let cursor: Json = copy;
  for (const part of parts.slice(0, -1)) {
    if (!cursor[part] || typeof cursor[part] !== "object") cursor[part] = {};
    cursor = cursor[part];
  }
  cursor[parts.at(-1)!] = value;
  return copy;
}

function valueAt(source: Json, path: string): any {
  return path.split(".").reduce<any>((value, part) => value?.[part], source);
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function AccountingGeneratorPage() {
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [templateId, setTemplateId] = useState("");
  const [template, setTemplate] = useState<TemplateItem | null>(null);
  const [schema, setSchema] = useState<FormSchema | null>(null);
  const [data, setData] = useState<Json>(initialData);
  const [previewUrl, setPreviewUrl] = useState("");
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get("templateId") || "";
    fetch(`${apiBase()}/v1/templates?category=finance`)
      .then((response) => response.json() as Promise<TemplateItem[]>)
      .then((items) => {
        const accounting = items.filter((item) => item.collection === "Accounting & Financial Documents");
        setTemplates(accounting);
        const selected = accounting.some((item) => item.id === requested) ? requested : accounting[0]?.id || "";
        setTemplateId(selected);
      })
      .catch(() => setMessage("Unable to load the accounting template library."));
  }, []);

  useEffect(() => {
    if (!templateId) return;
    setMessage("");
    Promise.all([
      fetch(`${apiBase()}/v1/templates/${encodeURIComponent(templateId)}`).then((response) => response.json()),
      fetch(`${apiBase()}/v1/accounting/templates/${encodeURIComponent(templateId)}/form`).then((response) => response.json()),
    ])
      .then(([selectedTemplate, form]: [TemplateItem, FormSchema]) => {
        setTemplate(selectedTemplate);
        setSchema(form);
        setData((current) => {
          let next = structuredClone(current);
          if (form.collectionPath && !Array.isArray(next[form.collectionPath])) {
            next[form.collectionPath] = [Object.fromEntries(form.collectionColumns.map((column) => [column.path, ""]))];
          }
          if (!next.document.number && form.documentPrefix) {
            next = setPath(next, "document.number", `${form.documentPrefix}-${new Date().getFullYear()}-000001`);
          }
          return next;
        });
      })
      .catch(() => setMessage("Unable to load the selected template."));
  }, [templateId]);

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  const collection = useMemo(() => {
    if (!schema?.collectionPath) return [];
    const rows = data[schema.collectionPath];
    return Array.isArray(rows) ? rows : [];
  }, [data, schema]);

  const update = (path: string, value: unknown) => setData((current) => setPath(current, path, value));

  const updateRow = (index: number, path: string, value: unknown) => {
    if (!schema?.collectionPath) return;
    setData((current) => {
      const next = structuredClone(current);
      const rows = Array.isArray(next[schema.collectionPath!]) ? next[schema.collectionPath!] : [];
      rows[index] = { ...(rows[index] || {}), [path]: value };
      next[schema.collectionPath!] = rows;
      return next;
    });
  };

  const addRow = () => {
    if (!schema?.collectionPath) return;
    setData((current) => {
      const next = structuredClone(current);
      const rows = Array.isArray(next[schema.collectionPath!]) ? next[schema.collectionPath!] : [];
      rows.push(Object.fromEntries(schema.collectionColumns.map((column) => [column.path, ""])));
      next[schema.collectionPath!] = rows;
      return next;
    });
  };

  const removeRow = (index: number) => {
    if (!schema?.collectionPath) return;
    setData((current) => {
      const next = structuredClone(current);
      next[schema.collectionPath!] = (next[schema.collectionPath!] || []).filter((_: unknown, rowIndex: number) => rowIndex !== index);
      return next;
    });
  };

  const preview = async () => {
    if (!templateId) return;
    setBusy("preview");
    setMessage("");
    try {
      const preparedResponse = await fetch(`${apiBase()}/v1/accounting/preview`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ templateId, data }),
      });
      if (!preparedResponse.ok) throw new Error(await preparedResponse.text());
      const prepared = (await preparedResponse.json()) as PreviewPayload;
      setData(prepared.data);

      const pdfResponse = await fetch(`${apiBase()}/v1/accounting/render`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ templateId, data: prepared.data, format: "pdf", persist: false }),
      });
      if (!pdfResponse.ok) throw new Error(await pdfResponse.text());
      const blob = await pdfResponse.blob();
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(URL.createObjectURL(blob));
      setMessage("Preview recalculated by the backend.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to preview document.");
    } finally {
      setBusy("");
    }
  };

  const issue = async (format: "pdf" | "docx") => {
    if (!templateId) return;
    setBusy(format);
    setMessage("");
    try {
      const response = await fetch(`${apiBase()}/v1/accounting/render`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ templateId, data, format, persist: true }),
      });
      if (!response.ok) throw new Error(await response.text());
      const blob = await response.blob();
      const number = String(valueAt(data, "document.number") || schema?.documentType || "accounting-document");
      downloadBlob(blob, `${number}.${format}`);
      const storedId = response.headers.get("X-Ithute-Document-Id");
      const verification = response.headers.get("X-Ithute-Verification-Code");
      setMessage(`Issued and archived${storedId ? ` as ${storedId}` : ""}${verification ? ` • ${verification}` : ""}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : `Unable to issue ${format.toUpperCase()}.`);
    } finally {
      setBusy("");
    }
  };

  return (
    <main className="accounting-generator">
      <header className="generator-topbar">
        <div>
          <span className="eyebrow">Ithute Studio • Accounting</span>
          <h1>Accounting Document Generator</h1>
          <p>Enter the financial data. Studio recalculates it and generates the official document on the backend.</p>
        </div>
        <div className="generator-actions">
          <Link className="ds-button" href="/templates">Template library</Link>
          <button className="ds-button" type="button" onClick={preview} disabled={!!busy}>{busy === "preview" ? "Preparing…" : "Preview PDF"}</button>
          <button className="ds-button primary" type="button" onClick={() => issue("pdf")} disabled={!!busy}>{busy === "pdf" ? "Issuing…" : "Issue PDF"}</button>
          <button className="ds-button" type="button" onClick={() => issue("docx")} disabled={!!busy}>{busy === "docx" ? "Issuing…" : "Issue DOCX"}</button>
        </div>
      </header>

      <section className="generator-template-bar">
        <label>
          <span>Template</span>
          <select value={templateId} onChange={(event) => setTemplateId(event.target.value)}>
            {templates.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
        <div><b>{template?.documentTypeLabel}</b><span>{template?.styleName}</span></div>
        {message && <p>{message}</p>}
      </section>

      <div className="generator-layout">
        <section className="generator-form">
          <div className="form-section">
            <h2>Business</h2>
            <div className="form-grid">
              <Field label="Company name" value={valueAt(data, "company.name")} onChange={(value) => update("company.name", value)} />
              <Field label="Registration number" value={valueAt(data, "company.registrationNumber")} onChange={(value) => update("company.registrationNumber", value)} />
              <Field label="Address" value={valueAt(data, "company.address")} onChange={(value) => update("company.address", value)} wide />
              <Field label="Phone" value={valueAt(data, "company.phone")} onChange={(value) => update("company.phone", value)} />
              <Field label="Email" value={valueAt(data, "company.email")} onChange={(value) => update("company.email", value)} />
            </div>
          </div>

          {schema?.showCounterparty && <div className="form-section">
            <h2>Account / Recipient</h2>
            <div className="form-grid">
              <Field label="Customer / supplier" value={valueAt(data, "counterparty.name")} onChange={(value) => update("counterparty.name", value)} />
              <Field label="Recipient" value={valueAt(data, "recipient.name")} onChange={(value) => update("recipient.name", value)} />
              <Field label="Recipient address" value={valueAt(data, "recipient.address")} onChange={(value) => update("recipient.address", value)} wide />
            </div>
          </div>}

          <div className="form-section">
            <h2>Document</h2>
            <div className="form-grid">
              <Field label="Document number" value={valueAt(data, "document.number")} onChange={(value) => update("document.number", value)} />
              <Field label="Reference" value={valueAt(data, "document.reference")} onChange={(value) => update("document.reference", value)} />
              <Field label="Date" type="date" value={valueAt(data, "document.date")} onChange={(value) => update("document.date", value)} />
              <Field label="Currency" value={valueAt(data, "document.currency")} onChange={(value) => update("document.currency", value.toUpperCase())} />
              <Field label="Notes" value={valueAt(data, "document.notes")} onChange={(value) => update("document.notes", value)} wide />
            </div>
          </div>

          {schema?.showLetterFields && <div className="form-section">
            <h2>Letter / Certificate Content</h2>
            <div className="form-grid">
              <Field label="Salutation" value={valueAt(data, "letter.salutation")} onChange={(value) => update("letter.salutation", value)} />
              <Field label="Confirmed balance" type="number" value={valueAt(data, "totals.balanceDue")} onChange={(value) => update("totals.balanceDue", Number(value || 0))} />
              <Field label="Body" value={valueAt(data, "letter.body")} onChange={(value) => update("letter.body", value)} wide />
              <Field label="Closing" value={valueAt(data, "letter.closing")} onChange={(value) => update("letter.closing", value)} />
            </div>
          </div>}

          {schema?.showPayrollFields && <div className="form-section">
            <h2>Employee</h2>
            <div className="form-grid">
              <Field label="Employee name" value={valueAt(data, "employee.name")} onChange={(value) => update("employee.name", value)} />
              <Field label="Employee number" value={valueAt(data, "employee.number")} onChange={(value) => update("employee.number", value)} />
              <Field label="Pay period" value={valueAt(data, "payroll.period")} onChange={(value) => update("payroll.period", value)} />
            </div>
          </div>}

          {schema?.collectionPath && <div className="form-section collection-section">
            <div className="section-title-row"><div><h2>{schema.collectionPath.replace(/([A-Z])/g, " $1")}</h2><p>{schema.documentTypeLabel} detail rows</p></div><button type="button" className="ds-button" onClick={addRow}>+ Add row</button></div>
            <div className="collection-table-wrap">
              <table className="collection-table">
                <thead><tr>{schema.collectionColumns.map((column) => <th key={column.path}>{column.label}</th>)}<th /></tr></thead>
                <tbody>{collection.map((row: Json, index: number) => <tr key={index}>
                  {schema.collectionColumns.map((column) => <td key={column.path}><input type={column.format === "currency" || column.format === "number" ? "number" : column.format === "date" ? "date" : "text"} step="0.01" value={row[column.path] ?? ""} onChange={(event) => updateRow(index, column.path, event.target.value)} /></td>)}
                  <td><button type="button" className="row-remove" onClick={() => removeRow(index)}>×</button></td>
                </tr>)}</tbody>
              </table>
            </div>
          </div>}

          {schema?.showPayrollFields && <PayrollRows title="Earnings" path="earnings" data={data} setData={setData} />}
          {schema?.showPayrollFields && <PayrollRows title="Deductions" path="deductions" data={data} setData={setData} />}

          <div className="form-section">
            <h2>Approval & Totals</h2>
            <div className="form-grid">
              <Field label="Prepared by" value={valueAt(data, "approval.preparedBy")} onChange={(value) => update("approval.preparedBy", value)} />
              <Field label="Approved by" value={valueAt(data, "approval.approvedBy")} onChange={(value) => update("approval.approvedBy", value)} />
              <Field label="Amount paid" type="number" value={valueAt(data, "totals.amountPaid")} onChange={(value) => update("totals.amountPaid", Number(value || 0))} />
              <Field label="Verification URL" value={valueAt(data, "verification.url")} onChange={(value) => update("verification.url", value)} />
            </div>
            <div className="totals-strip">
              <span>Subtotal <b>{data.document?.currency || ""} {Number(data.totals?.subtotal || 0).toFixed(2)}</b></span>
              <span>Tax <b>{data.document?.currency || ""} {Number(data.totals?.tax || 0).toFixed(2)}</b></span>
              <span>Total <b>{data.document?.currency || ""} {Number(data.totals?.total || 0).toFixed(2)}</b></span>
              <span>Balance <b>{data.document?.currency || ""} {Number(data.totals?.balanceDue || 0).toFixed(2)}</b></span>
            </div>
          </div>
        </section>

        <aside className="generator-preview">
          <div className="preview-heading"><div><b>Backend preview</b><span>{template?.name || "Select a template"}</span></div><button type="button" onClick={preview} disabled={!!busy}>Refresh</button></div>
          {previewUrl ? <iframe title="Accounting document PDF preview" src={previewUrl} /> : <div className="preview-placeholder"><strong>PDF Preview</strong><p>Enter the document information, then select Preview PDF. The preview is generated by FastAPI using the same renderer as the official file.</p></div>}
        </aside>
      </div>
    </main>
  );
}

function Field({ label, value, onChange, type = "text", wide = false }: { label: string; value: any; onChange: (value: string) => void; type?: string; wide?: boolean }) {
  return <label className={wide ? "field wide" : "field"}><span>{label}</span><input type={type} step={type === "number" ? "0.01" : undefined} value={value ?? ""} onChange={(event) => onChange(event.target.value)} /></label>;
}

function PayrollRows({ title, path, data, setData }: { title: string; path: string; data: Json; setData: (updater: (current: Json) => Json) => void }) {
  const rows = Array.isArray(data[path]) ? data[path] : [];
  return <div className="form-section collection-section"><div className="section-title-row"><h2>{title}</h2><button type="button" className="ds-button" onClick={() => setData((current) => ({ ...current, [path]: [...(current[path] || []), { description: "", amount: 0 }] }))}>+ Add row</button></div><div className="collection-table-wrap"><table className="collection-table"><thead><tr><th>Description</th><th>Amount</th><th /></tr></thead><tbody>{rows.map((row: Json, index: number) => <tr key={index}><td><input value={row.description || ""} onChange={(event) => setData((current) => { const next = structuredClone(current); next[path][index].description = event.target.value; return next; })} /></td><td><input type="number" step="0.01" value={row.amount ?? 0} onChange={(event) => setData((current) => { const next = structuredClone(current); next[path][index].amount = Number(event.target.value || 0); return next; })} /></td><td><button type="button" className="row-remove" onClick={() => setData((current) => ({ ...current, [path]: current[path].filter((_: unknown, rowIndex: number) => rowIndex !== index) }))}>×</button></td></tr>)}</tbody></table></div></div>;
}
