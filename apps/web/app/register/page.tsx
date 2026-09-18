"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import styles from "./register.module.css";

type Json = Record<string, any>;

const apiBase = () =>
  process.env.NEXT_PUBLIC_DOCUMENT_STUDIO_API || "http://localhost:8000";

function money(value: number | undefined) {
  return new Intl.NumberFormat("en-LS", {
    style: "currency",
    currency: "LSL",
  }).format(Number(value || 0));
}

export default function DocumentRegisterPage() {
  const [organizations, setOrganizations] = useState<Json[]>([]);
  const [organizationId, setOrganizationId] = useState("");
  const [dashboard, setDashboard] = useState<Json>({});
  const [documents, setDocuments] = useState<Json[]>([]);
  const [parties, setParties] = useState<Json[]>([]);
  const [message, setMessage] = useState("");
  const [showSetup, setShowSetup] = useState(false);

  const loadOrganizations = useCallback(async () => {
    const response = await fetch(`${apiBase()}/v1/operations/organizations`);
    if (!response.ok) throw new Error("Unable to load organizations.");
    const items = (await response.json()) as Json[];
    setOrganizations(items);
    setOrganizationId((current) => current || items[0]?.id || "");
    if (!items.length) setShowSetup(true);
  }, []);

  const loadRegister = useCallback(async (id: string) => {
    if (!id) return;
    const [dashboardResponse, documentsResponse, partiesResponse] = await Promise.all([
      fetch(`${apiBase()}/v1/operations/dashboard/${id}`),
      fetch(`${apiBase()}/v1/operations/documents?organizationId=${id}`),
      fetch(`${apiBase()}/v1/operations/parties?organizationId=${id}`),
    ]);
    if (!dashboardResponse.ok || !documentsResponse.ok || !partiesResponse.ok) {
      throw new Error("Unable to load the document register.");
    }
    setDashboard(await dashboardResponse.json());
    setDocuments(await documentsResponse.json());
    setParties(await partiesResponse.json());
  }, []);

  useEffect(() => {
    loadOrganizations().catch((error) => setMessage(error.message));
  }, [loadOrganizations]);

  useEffect(() => {
    if (!organizationId) return;
    loadRegister(organizationId).catch((error) => setMessage(error.message));
  }, [organizationId, loadRegister]);

  const createOrganization = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${apiBase()}/v1/operations/organizations`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        legalName: form.get("legalName"),
        tradingName: form.get("tradingName") || null,
        registrationNumber: form.get("registrationNumber") || null,
        tin: form.get("tin") || null,
        vatNumber: form.get("vatNumber") || null,
        vatRegistered: form.get("vatRegistered") === "on",
        defaultCurrency: "LSL",
        profile: {
          address: form.get("address") || "",
          phone: form.get("phone") || "",
          email: form.get("email") || "",
        },
        branding: {
          primaryColor: form.get("primaryColor") || "#102A43",
        },
        paymentTerms: form.get("paymentTerms") || null,
      }),
    });
    if (!response.ok) {
      setMessage(await response.text());
      return;
    }
    const item = await response.json();
    await loadOrganizations();
    setOrganizationId(item.id);
    setShowSetup(false);
    setMessage("Business profile created.");
  };

  const createParty = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!organizationId) return;
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${apiBase()}/v1/operations/parties`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        organizationId,
        kind: form.get("kind"),
        name: form.get("name"),
        tin: form.get("tin") || null,
        accountReference: form.get("accountReference") || null,
        contact: {
          email: form.get("email") || "",
          phone: form.get("phone") || "",
          address: form.get("address") || "",
        },
      }),
    });
    if (!response.ok) {
      setMessage(await response.text());
      return;
    }
    event.currentTarget.reset();
    await loadRegister(organizationId);
    setMessage("Customer/supplier added.");
  };

  const selected = organizations.find((item) => item.id === organizationId);

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}>ITHUTE STUDIO • OPERATIONS</span>
          <h1>Official Document Register</h1>
          <p>Number, approve, issue, track, relate and verify official business documents.</p>
        </div>
        <div className={styles.actions}>
          <Link className="ds-button" href="/">Studio home</Link>
          <Link className="ds-button" href="/templates">Templates</Link>
          <Link className="ds-button primary" href="/accounting/new">Create document</Link>
        </div>
      </header>

      <section className={styles.toolbar}>
        <label>
          <span>Organization</span>
          <select value={organizationId} onChange={(event) => setOrganizationId(event.target.value)}>
            <option value="">Select organization</option>
            {organizations.map((item) => (
              <option key={item.id} value={item.id}>{item.tradingName || item.legalName}</option>
            ))}
          </select>
        </label>
        <div className={styles.orgMeta}>
          <strong>{selected?.legalName || "No business profile yet"}</strong>
          <span>{selected?.tin ? `TIN ${selected.tin}` : "Create a business profile to begin issuing registered documents."}</span>
        </div>
        <button className="ds-button" type="button" onClick={() => setShowSetup((value) => !value)}>
          {showSetup ? "Close setup" : "Business setup"}
        </button>
      </section>

      {message && <div className={styles.message}>{message}</div>}

      {showSetup && (
        <section className={styles.setupGrid}>
          <form className={styles.panel} onSubmit={createOrganization}>
            <h2>Business profile & branding</h2>
            <div className={styles.formGrid}>
              <input name="legalName" required placeholder="Legal business name" />
              <input name="tradingName" placeholder="Trading name" />
              <input name="registrationNumber" placeholder="Registration number" />
              <input name="tin" placeholder="TIN" />
              <input name="vatNumber" placeholder="VAT number" />
              <label className={styles.check}><input name="vatRegistered" type="checkbox" /> VAT registered</label>
              <input name="address" placeholder="Business address" />
              <input name="phone" placeholder="Phone" />
              <input name="email" type="email" placeholder="Email" />
              <input name="primaryColor" placeholder="#102A43" defaultValue="#102A43" />
              <input className={styles.wide} name="paymentTerms" placeholder="Default payment terms" />
            </div>
            <button className="ds-button primary" type="submit">Save business profile</button>
          </form>

          <form className={styles.panel} onSubmit={createParty}>
            <h2>Customer / supplier address book</h2>
            <div className={styles.formGrid}>
              <select name="kind" defaultValue="customer"><option value="customer">Customer</option><option value="supplier">Supplier</option><option value="both">Both</option></select>
              <input name="name" required placeholder="Name" />
              <input name="tin" placeholder="TIN" />
              <input name="accountReference" placeholder="Account reference" />
              <input name="email" type="email" placeholder="Email" />
              <input name="phone" placeholder="Phone" />
              <input className={styles.wide} name="address" placeholder="Address" />
            </div>
            <button className="ds-button" type="submit" disabled={!organizationId}>Add party</button>
            <small>{parties.length} saved parties for this organization.</small>
          </form>
        </section>
      )}

      <section className={styles.metrics}>
        <Metric label="Registered documents" value={dashboard.documentCount || 0} />
        <Metric label="Amount issued" value={money(dashboard.amountIssued)} />
        <Metric label="Outstanding" value={money(dashboard.amountOutstanding)} />
        <Metric label="Overdue" value={dashboard.overdueDocuments || 0} />
        <Metric label="Awaiting approval" value={dashboard.awaitingApproval || 0} />
        <Metric label="Verifications" value={dashboard.verificationCount || 0} />
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div><h2>Document register</h2><p>Official numbers remain in the audit trail even when documents are voided.</p></div>
          <span>{documents.length} records</span>
        </div>
        <div className={styles.tableWrap}>
          <table>
            <thead><tr><th>Number</th><th>Type</th><th>Status</th><th>Issue date</th><th>Total</th><th>Balance</th><th>Actions</th></tr></thead>
            <tbody>
              {documents.map((item) => (
                <tr key={item.id}>
                  <td><strong>{item.documentNumber}</strong><small>Rev {item.revision}</small></td>
                  <td>{item.documentType}</td>
                  <td><span className={styles.status}>{item.status}</span></td>
                  <td>{item.issueDate || "—"}</td>
                  <td>{money(item.total)}</td>
                  <td>{money(item.balanceDue)}</td>
                  <td className={styles.rowActions}>
                    <a href={`${apiBase()}/v1/operations/documents/${item.id}/render?format=pdf`}>PDF</a>
                    <a href={`/verify/${item.verificationCode}`}>Verify</a>
                  </td>
                </tr>
              ))}
              {!documents.length && <tr><td colSpan={7} className={styles.empty}>No registered documents yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <article className={styles.metric}><span>{label}</span><strong>{value}</strong></article>;
}
