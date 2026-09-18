# Editor capabilities

Implemented in the first standalone core: A4/Letter paper sizing, portrait/landscape, zoom, ruler, margins, header/footer regions, page numbering preview, paragraph/headings, font family/size, bold/italic/underline, text/highlight colour, lists, text alignment, indentation, tables, images, hyperlinks, columns, watermark, text-box/signature/stamp/QR/chart nodes, print preview, Ctrl/Cmd+S, Ctrl/Cmd+P, autosave, undo/redo, variables, drag/drop data fields and dynamic table definitions.

## Pagination note

The editor uses physical page dimensions and explicit page-break nodes. Browser print/PDF honors those breaks. Automatic Word-style content reflow that moves overflow into independently editable page surfaces is intentionally isolated as a pagination subsystem rather than faked with fixed-height HTML. That subsystem can be added without changing Ithute Document Schema v1.
