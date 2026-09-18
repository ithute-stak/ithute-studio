# PDF Studio Architecture

Ithute PDF Studio imports an existing PDF into a non-destructive editing workspace.

## Core rule

The browser is an editing surface only. The authoritative PDF is always produced by the FastAPI backend.

## Project model

A PDF project contains:

- an immutable source PDF in backend-managed file storage;
- source-page metadata (width and height in PDF points);
- a page-order array used for reorder, duplicate, and delete-without-destroying-source workflows;
- optional page rotations;
- positioned edit layers stored in PostgreSQL JSONB;
- an optimistic version number so concurrent saves cannot silently overwrite each other.

The database schema is owned by Alembic. File storage is separate from PostgreSQL and is mounted persistently in Docker.

## Editing model

The current layer types are:

- `text` — positioned text, optionally covering the source area first;
- `cover` — an opaque visual cover/white-out;
- `highlight` — translucent rectangle;
- `rectangle` and `ellipse` — vector overlay shapes;
- `image` — inserted PNG/JPEG/WebP data.

PDFium is used to render source-page previews and discover positioned text objects. A source text object can be converted to a Studio text layer. The source PDF itself is never rewritten during editing.

## Backend export

Export runs only on the backend:

1. Read the immutable source with `pypdf`.
2. Rebuild output pages from `pageOrder`.
3. Draw edit layers with ReportLab using PDF coordinates.
4. Merge the overlay into each output page.
5. Apply configured page rotation.
6. Return a newly generated PDF.

This preserves the original source and keeps final output deterministic across clients.

## Redaction warning

A `cover` layer only hides source content visually. The original text/content may remain inside the PDF content stream and may still be extractable.

Do **not** market or label visual cover as secure redaction.

A future secure-redaction mode must physically remove or rasterize the affected source content before export and must have dedicated tests proving that redacted text cannot be recovered through text extraction.

## Next PDF Studio phases

- secure redaction and irreversible flattening;
- image-object extraction/replacement;
- vector path selection and editing;
- crop/resize canvas controls;
- form-field editing and flattening;
- annotations, comments, links, bookmarks and attachments;
- signatures and certificate-aware workflows;
- OCR for scanned PDFs;
- page insertion from PDF/image sources;
- asset storage instead of embedding large image data in JSONB;
- undo/redo snapshots and revision history;
- background rendering jobs for large PDFs;
- font substitution/embedding controls;
- permission/encryption handling;
- optional low-level object editor for advanced users.
