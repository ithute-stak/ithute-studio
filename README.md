# Ithute Document Studio

Standalone, product-neutral document creation platform for the Ithute ecosystem.

## What is included

This repository intentionally contains **no product-specific connector logic**. The core works with generic workspaces, templates, documents, data dictionaries and records.

The first standalone implementation includes:

- Tiptap 3 Word-like editor foundation with real A4/Letter dimensions, portrait/landscape, margins, zoom and ruler.
- Header, body and footer editing regions, page-number settings and watermarks.
- Paragraph/headings, font family/size, bold/italic/underline, text colour, highlighting, lists, alignment and indentation.
- Tables, borders/shading, images, hyperlinks, columns and explicit page breaks.
- Structured text boxes, logos, letterheads, stamps, signatures, QR-code and chart objects.
- Document properties panel.
- Browser print preview plus keyboard shortcuts (`Ctrl/Cmd+S`, `Ctrl/Cmd+P`).
- Autosave contract, versioned saves and conflict protection.
- Template catalogue model with the requested generic categories.
- `{{path.to.value}}` variables and first-class variable nodes.
- Collection-backed dynamic tables.
- Generic searchable/drag-and-drop Data panel driven only by a data dictionary.
- Interactive editing and programmatic `POST /v1/documents/from-template` generation.
- Persistent generic template/document API using SQLite for this standalone foundation.
- Server-side HTML, PDF and DOCX export, with page size/orientation/margins, headers/footers, page numbering, watermark, tables, page breaks and QR rendering.
- Separate renderer, signature, verification, worker and JavaScript/Python SDK boundaries.

## Repository layout

```text
apps/
  web/       Next.js Studio UI
  api/       FastAPI document/template API
  worker/    rendering/bulk-job worker boundary
packages/
  editor/             reusable Tiptap editor package
  document-schema/    canonical Ithute Document Schema v1
  template-engine/    variable and dynamic-table resolver
  renderer/           rendering contract + HTML renderer
  signature-engine/   signature contract
  verification/       SHA-256 verification contract
  sdk-js/             JavaScript client
  sdk-python/         Python client
```

## Run locally

```bash
corepack enable
pnpm install
pnpm dev
```

In another terminal:

```bash
cd apps/api
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

Or use:

```bash
docker compose up --build
```

Web: `http://localhost:3000`  
API/OpenAPI: `http://localhost:8000/docs`

## Generic automatic generation

```http
POST /v1/documents/from-template
Content-Type: application/json
```

```json
{
  "templateId": "template-id",
  "data": {
    "organization": { "name": "Example Organization" },
    "contact": { "fullName": "Sample Person" },
    "items": [
      { "description": "Item one", "quantity": 2, "total": 100 }
    ]
  }
}
```

No source application is assumed. Later connectors only provide approved data and a data dictionary.

## Pagination decision

This open core uses physical paper dimensions and explicit page-break nodes today. True automatic Word-style pagination is intentionally isolated rather than faked. Tiptap's official Pages extension can provide automatic pagination, repeating headers/footers and pagination-safe tables, but it currently requires Tiptap Team/private-registry access. A future `pagination` adapter can use that package or an Ithute-owned reflow implementation without changing **Ithute Document Schema v1**.

## Architectural rule

Applications do not own document editing/rendering logic. Document Studio owns documents. Future integrations expose approved data dictionaries and records; no connector-specific code belongs in the editor, schema, template engine or renderer core.
