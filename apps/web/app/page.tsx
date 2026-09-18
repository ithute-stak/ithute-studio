import Link from "next/link";
const capabilities = [
  ["Word-like editing", "A4/Letter pages, rulers, margins, headers, footers, tables, images, columns, page breaks and print preview."],
  ["Reusable templates", "Build reusable documents with neutral variables such as {{organization.name}} and {{record.reference}}."],
  ["Dynamic tables", "Bind repeating collections to table definitions and expand them during document generation."],
  ["Data panel", "Browse or drag generic fields into the document. Future connectors only need to publish a data dictionary."],
  ["Automation API", "Generate documents from a template plus a data payload without coupling the core to a specific product."],
  ["Reusable package", "The editor ships as @ithute/document-editor so other Ithute apps can embed the exact same Studio surface later."],
];
export default function Home(){return <main className="ds-home"><header><div className="ds-brand"><b>I</b><span><strong>Ithute Document Studio</strong><small>Document creation platform</small></span></div><div className="ds-actions"><Link className="ds-button" href="/templates">Templates</Link><Link className="ds-button primary" href="/editor">Open editor</Link></div></header><section className="ds-hero"><h1>Professional documents, built once and reusable everywhere.</h1><p>The Studio core is product-neutral. It edits structured documents, binds template data, renders dynamic tables and exposes clean APIs. Connectors can be added later without changing the editor.</p><div className="ds-actions"><Link className="ds-button primary" href="/editor">Create a document</Link><Link className="ds-button" href="/templates">Browse templates</Link></div></section><section className="ds-grid">{capabilities.map(([h,p])=><article key={h} className="ds-card"><h3>{h}</h3><p>{p}</p></article>)}</section></main>}
