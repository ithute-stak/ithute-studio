# Ithute Document Studio architecture

The Studio core is deliberately domain-neutral. A document is structured content plus page settings, properties, variables and an optional source reference. No business-product name is permitted in core schema, editor extensions, API routes or rendering interfaces.

## Runtime boundaries

- `apps/web`: Next.js shell and template library.
- `apps/api`: FastAPI document/template API.
- `apps/worker`: asynchronous rendering and bulk-generation boundary.
- `packages/document-schema`: canonical Ithute Document Schema v1.
- `packages/editor`: embeddable Tiptap Word-like editor.
- `packages/template-engine`: variables and repeating/dynamic tables.
- `packages/renderer`: format-neutral renderer interface plus HTML renderer; the FastAPI rendering service currently produces HTML, PDF and DOCX.
- `packages/signature-engine`: signature-field discovery/completion rules.
- `packages/verification`: deterministic hashing and verification records.
- `packages/sdk-js` / `packages/sdk-python`: integration clients.

## Connector contract (later)

A connector only needs to provide a neutral `DataDictionary`, record data and optional source metadata. The editor never imports connector code.
