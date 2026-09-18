import type { IthuteDocumentV1, TiptapJson } from "@ithute/document-schema";

export function getPath(data: unknown, path: string): unknown {
  if (!path) return data;
  return path.split(".").reduce<unknown>((current, key) => {
    if (current && typeof current === "object" && key in current) return (current as Record<string, unknown>)[key];
    return undefined;
  }, data);
}

export function formatValue(value: unknown, format?: string): string {
  if (value == null) return "";
  if (format === "currency" && typeof value === "number") return new Intl.NumberFormat(undefined, { style: "currency", currency: "LSL" }).format(value);
  if (format === "date") {
    const date = value instanceof Date ? value : new Date(String(value));
    return Number.isNaN(date.valueOf()) ? String(value) : new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
  }
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

export function resolveText(text: string, data: unknown): string {
  return text.replace(/\{\{\s*([\w.[\]-]+)\s*\}\}/g, (_full, path: string) => formatValue(getPath(data, path)));
}

export function resolveNode(node: TiptapJson, data: unknown): TiptapJson | TiptapJson[] {
  if (node.type === "variable") {
    const path = String(node.attrs?.path || "");
    const format = typeof node.attrs?.format === "string" ? node.attrs.format : undefined;
    return { type: "text", text: formatValue(getPath(data, path), format) };
  }

  if (node.type === "dynamicTable") {
    const path = String(node.attrs?.collectionPath || "");
    const rows = getPath(data, path);
    const columns = Array.isArray(node.attrs?.columns) ? node.attrs?.columns as Array<{label:string; path:string; format?:string}> : [];
    const items = Array.isArray(rows) ? rows : [];
    return {
      type: "table",
      content: [
        { type: "tableRow", content: columns.map((col) => ({ type: "tableHeader", content: [{ type: "paragraph", content: [{ type: "text", text: col.label }] }] })) },
        ...items.map((item) => ({
          type: "tableRow",
          content: columns.map((col) => ({ type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: formatValue(getPath(item, col.path), col.format) }] }] }))
        }))
      ]
    };
  }

  const next: TiptapJson = { ...node };
  if (typeof next.text === "string") next.text = resolveText(next.text, data);
  if (next.content) {
    next.content = next.content.flatMap((child) => {
      const resolved = resolveNode(child, data);
      return Array.isArray(resolved) ? resolved : [resolved];
    });
  }
  return next;
}

export function resolveDocument(template: IthuteDocumentV1, data: Record<string, unknown>): IthuteDocumentV1 {
  return {
    ...template,
    header: resolveNode(template.header, data) as TiptapJson,
    body: resolveNode(template.body, data) as TiptapJson,
    footer: resolveNode(template.footer, data) as TiptapJson,
    variables: data,
    templateId: template.templateId || template.id,
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    version: 1
  };
}
