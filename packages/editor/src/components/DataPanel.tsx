"use client";
import { useMemo, useState } from "react";
import type { DataDictionary, DataDictionaryField } from "@ithute/document-schema";

export const ITHUTE_DATA_FIELD_MIME = "application/x-ithute-data-field";

function FieldRow({ field, onInsert }: { field: DataDictionaryField; onInsert: (field: DataDictionaryField) => void }) {
  const [open, setOpen] = useState(true);
  const children = field.type === "collection" ? field.itemFields : field.children;
  return <div className="ithute-data-field-wrap">
    <div className="ithute-data-field" draggable onDragStart={(event) => {
      event.dataTransfer.setData(ITHUTE_DATA_FIELD_MIME, JSON.stringify(field));
      event.dataTransfer.effectAllowed = "copy";
    }}>
      {children?.length ? <button type="button" className="ithute-data-expand" onClick={() => setOpen((v) => !v)}>{open ? "▾" : "▸"}</button> : <span className="ithute-data-expand-spacer" />}
      <button type="button" className="ithute-data-field-main" onClick={() => onInsert(field)}>
        <strong>{field.label}</strong><small>{field.path}</small>
      </button>
      <span className="ithute-data-type">{field.type}</span>
    </div>
    {open && children?.length ? <div className="ithute-data-children">{children.map((child) => <FieldRow key={`${field.path}.${child.path}`} field={{...child, path: field.type === "collection" ? child.path : `${field.path}.${child.path}`}} onInsert={onInsert} />)}</div> : null}
  </div>;
}

export function DataPanel({ dictionary, onInsert }: { dictionary?: DataDictionary; onInsert: (field: DataDictionaryField) => void }) {
  const [query, setQuery] = useState("");
  const fields = useMemo(() => {
    if (!dictionary || !query.trim()) return dictionary?.fields || [];
    const q = query.toLowerCase();
    return dictionary.fields.filter((f) => `${f.label} ${f.path}`.toLowerCase().includes(q));
  }, [dictionary, query]);
  return <aside className="ithute-data-panel">
    <div className="ithute-panel-heading"><div><strong>Data</strong><small>{dictionary?.name || "No data dictionary"}</small></div></div>
    <input className="ithute-panel-search" placeholder="Search fields" value={query} onChange={(e) => setQuery(e.target.value)} />
    <div className="ithute-data-list">
      {fields.length ? fields.map((field) => <FieldRow key={field.path} field={field} onInsert={onInsert} />) : <p className="ithute-panel-empty">Fields from future connectors will appear here. The editor itself stays product-neutral.</p>}
    </div>
  </aside>;
}
