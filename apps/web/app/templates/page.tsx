"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type TemplateItem = {
  id: string;
  name: string;
  description?: string;
  category?: string;
  collection?: string;
  documentType?: string;
  documentTypeLabel?: string;
  stylePreset?: string;
  styleName?: string;
  style?: {
    primaryColor?: string;
    secondaryColor?: string;
    accentColor?: string;
  };
  isBuiltIn?: boolean;
};

type CatalogMeta = {
  templateCount: number;
  documentTypeCount: number;
  styleCount: number;
  styles: Array<{ slug: string; name: string; primaryColor: string; accentColor: string }>;
  documentTypes: Array<{ slug: string; name: string }>;
};

const apiBase = () => process.env.NEXT_PUBLIC_DOCUMENT_STUDIO_API || "http://localhost:8000";

export default function Templates() {
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [catalog, setCatalog] = useState<CatalogMeta | null>(null);
  const [query, setQuery] = useState("");
  const [type, setType] = useState("all");
  const [style, setStyle] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${apiBase()}/v1/templates?category=finance`).then((response) => {
        if (!response.ok) throw new Error("Unable to load templates");
        return response.json() as Promise<TemplateItem[]>;
      }),
      fetch(`${apiBase()}/v1/templates/catalog/accounting`).then((response) => {
        if (!response.ok) throw new Error("Unable to load accounting catalog");
        return response.json() as Promise<CatalogMeta>;
      }),
    ])
      .then(([items, metadata]) => {
        setTemplates(items.filter((item) => item.collection === "Accounting & Financial Documents"));
        setCatalog(metadata);
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return templates.filter((item) => {
      if (type !== "all" && item.documentType !== type) return false;
      if (style !== "all" && item.stylePreset !== style) return false;
      if (!needle) return true;
      return `${item.name} ${item.description || ""}`.toLowerCase().includes(needle);
    });
  }, [templates, query, type, style]);

  return (
    <main className="templates-page accounting-library">
      <section className="templates-head accounting-hero">
        <div>
          <span className="eyebrow">Ithute Studio • Built-in collection</span>
          <h1>Accounting & Financial Documents</h1>
          <p>
            {catalog
              ? `${catalog.documentTypeCount} document types × ${catalog.styleCount} professional designs = ${catalog.templateCount} ready-to-use templates.`
              : "Professional backend-rendered accounting templates with reusable data bindings."}
          </p>
        </div>
        <Link className="ds-button primary" href="/accounting/new">New accounting document</Link>
      </section>

      {catalog && (
        <section className="accounting-styles" aria-label="Design systems">
          {catalog.styles.map((item) => (
            <button
              key={item.slug}
              className={style === item.slug ? "style-chip active" : "style-chip"}
              onClick={() => setStyle(style === item.slug ? "all" : item.slug)}
              type="button"
            >
              <span className="style-swatch" style={{ background: item.primaryColor }} />
              <span>{item.name}</span>
              <i style={{ background: item.accentColor }} />
            </button>
          ))}
        </section>
      )}

      <section className="template-toolbar">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search invoice, ledger, payroll, statement…"
          aria-label="Search accounting templates"
        />
        <select value={type} onChange={(event) => setType(event.target.value)}>
          <option value="all">All document types</option>
          {catalog?.documentTypes.map((item) => (
            <option key={item.slug} value={item.slug}>{item.name}</option>
          ))}
        </select>
        <select value={style} onChange={(event) => setStyle(event.target.value)}>
          <option value="all">All styles</option>
          {catalog?.styles.map((item) => (
            <option key={item.slug} value={item.slug}>{item.name}</option>
          ))}
        </select>
        <strong>{filtered.length} templates</strong>
      </section>

      {loading ? (
        <div className="template-empty">Loading accounting template library…</div>
      ) : (
        <section className="templates-grid accounting-grid">
          {filtered.map((item) => {
            const primary = item.style?.primaryColor || "#334155";
            const secondary = item.style?.secondaryColor || "#f1f5f9";
            const accent = item.style?.accentColor || "#64748b";
            return (
              <article className="template-card accounting-card" key={item.id}>
                <div className="template-preview" style={{ background: secondary }}>
                  <div className="preview-header" style={{ background: primary }}>
                    <span />
                    <b>{item.documentTypeLabel}</b>
                  </div>
                  <div className="preview-title" style={{ color: primary }}>{item.documentTypeLabel}</div>
                  <div className="preview-lines"><i /><i /><i /></div>
                  <div className="preview-table">
                    <span style={{ background: primary }} />
                    <i /><i /><i />
                  </div>
                  <div className="preview-footer" style={{ borderColor: accent }} />
                </div>
                <div className="template-card-body">
                  <div className="template-tags">
                    <span>{item.documentTypeLabel}</span>
                    <span>{item.styleName}</span>
                  </div>
                  <h3>{item.name}</h3>
                  <p>{item.description}</p>
                  <Link className="template-open" href={`/accounting/new?templateId=${item.id}`}>Use template →</Link>
                </div>
              </article>
            );
          })}
        </section>
      )}

      {!loading && filtered.length === 0 && (
        <div className="template-empty">No templates match the current filters.</div>
      )}
    </main>
  );
}
