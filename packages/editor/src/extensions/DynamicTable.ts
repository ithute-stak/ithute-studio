import { Node, mergeAttributes } from "@tiptap/core";
export type DynamicColumn = { label: string; path: string; format?: string };
export const DynamicTable = Node.create({
  name: "dynamicTable", group: "block", atom: true, selectable: true, draggable: true,
  addAttributes() { return { collectionPath: { default: "items" }, label: { default: "Dynamic table" }, columns: { default: [] as DynamicColumn[] } }; },
  parseHTML: () => [{ tag: "div[data-ithute-dynamic-table]", getAttrs: (el) => {
    const e = el as HTMLElement; let columns: DynamicColumn[] = [];
    try { columns = JSON.parse(e.dataset.columns || "[]"); } catch { columns = []; }
    return { collectionPath: e.dataset.collectionPath || "items", label: e.dataset.label || "Dynamic table", columns };
  }}],
  renderHTML: ({ HTMLAttributes }) => ["div", mergeAttributes({
    "data-ithute-dynamic-table": "true", "data-collection-path": HTMLAttributes.collectionPath,
    "data-label": HTMLAttributes.label, "data-columns": JSON.stringify(HTMLAttributes.columns || []), class: "ithute-dynamic-table"
  }), ["strong", {}, HTMLAttributes.label], ["span", {}, `Repeats from {{${HTMLAttributes.collectionPath}}}`]]
});
