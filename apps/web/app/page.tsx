import Link from "next/link";

const capabilities = [
  ["Word-like editing", "A4/Letter pages, rulers, margins, headers, footers, tables, images, columns, page breaks and print preview."],
  ["PDF Studio", "Upload an existing PDF, select source text, add editable layers, rearrange pages and export a new backend-rendered PDF."],
  ["Lesotho template library", "Browse law-aware HR, legal, lending, procurement, fleet, construction, education, risk, payments, property, insurance and institutional templates."],
  ["Reusable templates", "Build reusable documents with neutral variables such as {{organization.name}} and {{record.reference}}."],
  ["Dynamic tables", "Bind repeating collections to table definitions and expand them during document generation."],
  ["Data panel", "Browse or drag generic fields into the document. Future connectors only need to publish a data dictionary."],
  ["Automation API", "Generate documents from a template plus a data payload without coupling the core to a specific product."],
  ["Reusable package", "The editor ships as @ithute/document-editor so other Ithute apps can embed the exact same Studio surface later."],
];

export default function Home() {
  return (
    <main className="ds-home">
      <header>
        <div className="ds-brand"><b>I</b><span><strong>Ithute Document Studio</strong><small>Document creation platform</small></span></div>
        <div className="ds-actions"><Link className="ds-button" href="/pdf-editor">PDF Studio</Link><Link className="ds-button" href="/templates/lesotho">Lesotho templates</Link><Link className="ds-button" href="/templates">Accounting</Link><Link className="ds-button primary" href="/editor">Open editor</Link></div>
      </header>
      <section className="ds-hero">
        <h1>Create documents. Edit PDFs. Render everything from the backend.</h1>
        <p>The Studio core is product-neutral. It edits structured documents, imports existing PDFs into a layer-based workspace, binds template data and keeps the backend authoritative for final PDF and DOCX generation.</p>
        <div className="ds-actions"><Link className="ds-button primary" href="/editor">Create a document</Link><Link className="ds-button" href="/templates/lesotho">Browse Lesotho templates</Link><Link className="ds-button" href="/pdf-editor">Edit a PDF</Link><Link className="ds-button" href="/templates">Accounting templates</Link></div>
      </section>
      <section className="ds-grid">{capabilities.map(([heading, text]) => <article key={heading} className="ds-card"><h3>{heading}</h3><p>{text}</p></article>)}</section>
    </main>
  );
}
