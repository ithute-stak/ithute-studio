import type { IthuteDocumentV1, TiptapJson } from "@ithute/document-schema";
export type RenderFormat = "html" | "pdf" | "docx";
export interface RenderResult { format: RenderFormat; mimeType: string; bytes: Uint8Array; fileName: string; }
export interface DocumentRenderer { render(document: IthuteDocumentV1, format: RenderFormat): Promise<RenderResult>; }

function esc(value: unknown) { return String(value ?? "").replace(/[&<>\"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c] || c)); }
function renderNode(node: TiptapJson): string {
  const content=(node.content||[]).map(renderNode).join(""); const a=(node.attrs||{}) as Record<string,unknown>;
  switch(node.type){
    case "doc": return content; case "text": return esc(node.text||""); case "paragraph": return `<p>${content||"<br>"}</p>`;
    case "heading": {const l=Math.min(6,Math.max(1,Number(a.level||1)));return `<h${l}>${content}</h${l}>`;}
    case "bulletList": return `<ul>${content}</ul>`; case "orderedList": return `<ol>${content}</ol>`; case "listItem": return `<li>${content}</li>`;
    case "table": return `<table>${content}</table>`; case "tableRow": return `<tr>${content}</tr>`; case "tableHeader": return `<th>${content}</th>`; case "tableCell": return `<td>${content}</td>`;
    case "pageBreak": return `<div class="page-break"></div>`; case "image": return `<img src="${esc(a.src)}" alt="${esc(a.alt)}">`;
    case "signature": case "stamp": case "qrCode": case "chart": case "textBox": return `<div class="studio-object studio-${node.type}">${esc(a.label||node.type)}</div>`;
    default: return content;
  }
}
export function renderDocumentHtml(document:IthuteDocumentV1){
  const m=document.settings.marginsMm; const css=`@page{margin:${m.top}mm ${m.right}mm ${m.bottom}mm ${m.left}mm}body{font-family:Arial,sans-serif;color:#111;line-height:1.45}table{border-collapse:collapse;width:100%}th,td{border:1px solid #aaa;padding:6px}.page-break{break-after:page}.studio-object{border:1px dashed #777;padding:8px;margin:8px 0}img{max-width:100%}`;
  return `<!doctype html><html><head><meta charset="utf-8"><title>${esc(document.properties.title)}</title><style>${css}</style></head><body><header>${renderNode(document.header)}</header><main>${renderNode(document.body)}</main><footer>${renderNode(document.footer)}</footer></body></html>`;
}
