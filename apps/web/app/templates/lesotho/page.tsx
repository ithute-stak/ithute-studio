"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type Law = { title: string; citation: string; authority: string; sourceUrl: string };
type Pack = {
  slug: string;
  name: string;
  category: string;
  documentTypeCount: number;
  templateCount: number;
  riskLevel: string;
  laws: Law[];
};
type Style = { slug: string; name: string; primaryColor: string; secondaryColor: string; accentColor: string };
type Catalog = {
  jurisdiction: string;
  lawProfileVersion: string;
  packCount: number;
  documentTypeCount: number;
  styleCount: number;
  templateCount: number;
  packs: Pack[];
  styles: Style[];
};
type Template = {
  id: string;
  name: string;
  description: string;
  collection: string;
  pack: string;
  documentType: string;
  documentTypeLabel: string;
  stylePreset: string;
  styleName: string;
  style: Style;
  compliance: {
    riskLevel: string;
    legalReviewRequired: boolean;
    laws: Law[];
    requiredChecks: string[];
  };
};

const apiBase = () => process.env.NEXT_PUBLIC_DOCUMENT_STUDIO_API || "http://localhost:8000";

export default function LesothoTemplatesPage() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [pack, setPack] = useState("all");
  const [style, setStyle] = useState("all");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${apiBase()}/v1/templates/catalog/lesotho`).then((response) => {
        if (!response.ok) throw new Error("Unable to load Lesotho template catalog");
        return response.json() as Promise<Catalog>;
      }),
      fetch(`${apiBase()}/v1/templates`).then((response) => {
        if (!response.ok) throw new Error("Unable to load templates");
        return response.json() as Promise<Template[]>;
      }),
    ])
      .then(([metadata, items]) => {
        setCatalog(metadata);
        setTemplates(items.filter((item) => Boolean(item.pack)));
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return templates.filter((item) => {
      if (pack !== "all" && item.pack !== pack) return false;
      if (style !== "all" && item.stylePreset !== style) return false;
      if (!needle) return true;
      return `${item.name} ${item.description} ${item.collection}`.toLowerCase().includes(needle);
    });
  }, [templates, pack, style, query]);

  return (
    <main className="templates-page accounting-library">
      <section className="templates-head accounting-hero">
        <div>
          <span className="eyebrow">Ithute Studio • Kingdom of Lesotho</span>
          <h1>Lesotho Business & Institutional Templates</h1>
          <p>
            {catalog
              ? `${catalog.packCount} packs • ${catalog.documentTypeCount} document types • ${catalog.styleCount} professional designs • ${catalog.templateCount} law-aware templates.`
              : "Law-aware document templates mapped to the current Lesotho legal framework."}
          </p>
          {catalog && <p><strong>Compliance profile:</strong> {catalog.lawProfileVersion}. Execution-sensitive documents still require transaction-specific validation.</p>}
        </div>
        <div className="ds-actions">
          <Link className="ds-button" href="/templates">Accounting templates</Link>
          <Link className="ds-button primary" href="/editor">Blank document</Link>
        </div>
      </section>

      {catalog && (
        <section className="accounting-styles" aria-label="Template packs">
          <button className={pack === "all" ? "style-chip active" : "style-chip"} onClick={() => setPack("all")} type="button">All packs</button>
          {catalog.packs.map((item) => (
            <button key={item.slug} className={pack === item.slug ? "style-chip active" : "style-chip"} onClick={() => setPack(item.slug)} type="button">
              <span>{item.name}</span><i style={{ background: item.riskLevel === "high" ? "#7f1d1d" : "#64748b" }} />
            </button>
          ))}
        </section>
      )}

      <section className="template-toolbar">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search contract, KYC, fleet, certificate…" aria-label="Search Lesotho templates" />
        <select value={pack} onChange={(event) => setPack(event.target.value)}>
          <option value="all">All packs</option>
          {catalog?.packs.map((item) => <option key={item.slug} value={item.slug}>{item.name}</option>)}
        </select>
        <select value={style} onChange={(event) => setStyle(event.target.value)}>
          <option value="all">All styles</option>
          {catalog?.styles.map((item) => <option key={item.slug} value={item.slug}>{item.name}</option>)}
        </select>
        <strong>{filtered.length} templates</strong>
      </section>

      {loading ? (
        <div className="template-empty">Loading Lesotho template library…</div>
      ) : (
        <section className="templates-grid accounting-grid">
          {filtered.map((item) => {
            const primary = item.style?.primaryColor || "#334155";
            const secondary = item.style?.secondaryColor || "#f1f5f9";
            const accent = item.style?.accentColor || "#64748b";
            return (
              <article className="template-card accounting-card" key={item.id}>
                <div className="template-preview" style={{ background: secondary }}>
                  <div className="preview-header" style={{ background: primary }}><span /><b>LESOTHO • {item.collection}</b></div>
                  <div className="preview-title" style={{ color: primary }}>{item.documentTypeLabel}</div>
                  <div className="preview-lines"><i /><i /><i /></div>
                  <div className="preview-table"><span style={{ background: primary }} /><i /><i /><i /></div>
                  <div className="preview-footer" style={{ borderColor: accent }} />
                </div>
                <div className="template-card-body">
                  <div className="template-tags">
                    <span>{item.collection}</span><span>{item.styleName}</span><span>Lesotho law-aware</span>
                    {item.compliance?.legalReviewRequired && <span>Legal review</span>}
                  </div>
                  <h3>{item.name}</h3>
                  <p>{item.description}</p>
                  <p><strong>{item.compliance?.laws?.length || 0}</strong> governing-law sources • risk {item.compliance?.riskLevel || "standard"}</p>
                  <Link className="template-open" href={`/editor?templateId=${item.id}`}>Use template →</Link>
                </div>
              </article>
            );
          })}
        </section>
      )}

      {!loading && filtered.length === 0 && <div className="template-empty">No templates match the current filters.</div>}
    </main>
  );
}
