import { Node, mergeAttributes } from "@tiptap/core";
export const Variable = Node.create({
  name: "variable", group: "inline", inline: true, atom: true, selectable: true,
  addAttributes() { return { path: { default: "" }, label: { default: "Variable" }, format: { default: null } }; },
  parseHTML: () => [{ tag: "span[data-ithute-variable]", getAttrs: (el) => ({ path: (el as HTMLElement).dataset.path, label: (el as HTMLElement).dataset.label, format: (el as HTMLElement).dataset.format || null }) }],
  renderHTML: ({ HTMLAttributes }) => ["span", mergeAttributes({
    "data-ithute-variable": "true", "data-path": HTMLAttributes.path, "data-label": HTMLAttributes.label,
    "data-format": HTMLAttributes.format || "", class: "ithute-variable-chip", contenteditable: "false"
  }), `{{${HTMLAttributes.path}}}`]
});
