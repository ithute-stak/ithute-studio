import { Node, mergeAttributes } from "@tiptap/core";
export const PageBreak = Node.create({
  name: "pageBreak", group: "block", atom: true, selectable: true,
  parseHTML: () => [{ tag: "div[data-ithute-page-break]" }],
  renderHTML: ({ HTMLAttributes }) => ["div", mergeAttributes(HTMLAttributes, { "data-ithute-page-break": "true", class: "ithute-page-break" })]
});
